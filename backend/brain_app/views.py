from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from . import flashcards as flashcards_module
from . import graph as graph_module
from . import qa as qa_module
from .ingest import ingest_folder
from .vectorstore import collection_stats
import zipfile
import tempfile
import shutil
import os

def index(request):
    return render(request, 'index.html')

@api_view(['GET'])
def root(request):
    return Response({"status": "ok", "service": "developer-brain-api-django"})

@api_view(['GET'])
def stats(request):
    return Response(collection_stats())

@api_view(['POST'])
def ingest(request):
    folder = request.data.get('folder')
    if not folder:
        return Response({"detail": "folder path is required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        result = ingest_folder(folder)
        return Response(result)
    except FileNotFoundError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def ask(request):
    question = request.data.get('question')
    top_k = request.data.get('top_k')
    if not question or not question.strip():
        return Response({"detail": "question must not be empty"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        return Response(qa_module.qa(question, top_k=top_k))
    except Exception as e:
        return Response({"detail": f"Query failed: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def flashcards(request):
    n = request.query_params.get('n', 5)
    try:
        n = int(n)
    except ValueError:
        n = 5
    return Response({"flashcards": flashcards_module.generate_flashcards(n)})

@api_view(['POST'])
def build_graph(request):
    limit = request.data.get('limit', 200)
    try:
        limit = int(limit)
    except ValueError:
        limit = 200
    try:
        return Response(graph_module.build_graph(limit=limit))
    except Exception as e:
        return Response({"detail": f"Graph build failed: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_graph(request):
    limit = request.query_params.get('limit', 300)
    try:
        limit = int(limit)
    except ValueError:
        limit = 300
    try:
        return Response(graph_module.get_graph_data(limit=limit))
    except Exception as e:
        return Response({"detail": f"Could not read graph: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
def clear_graph(request):
    try:
        graph_module.clear_graph()
        return Response({"status": "cleared"})
    except Exception as e:
        return Response({"detail": f"Could not clear graph: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def ingest_upload(request):
    if 'file' not in request.FILES:
        return Response({"detail": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
    
    uploaded_file = request.FILES['file']
    if not uploaded_file.name.endswith('.zip'):
        return Response({"detail": "Only .zip files are supported"}, status=status.HTTP_400_BAD_REQUEST)

    # Create a temporary directory to extract the ZIP
    temp_dir = tempfile.mkdtemp()
    try:
        zip_path = os.path.join(temp_dir, 'upload.zip')
        with open(zip_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        extract_dir = os.path.join(temp_dir, 'extracted')
        os.makedirs(extract_dir)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Ingest the extracted folder
        result = ingest_folder(extract_dir)
        return Response(result)
    except Exception as e:
        return Response({"detail": f"Ingestion failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        # Clean up temporary files
        shutil.rmtree(temp_dir)
