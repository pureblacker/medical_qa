import warnings
warnings.filterwarnings("ignore")
import os
import torch
from backend.config.config import load_nested_params
from langchain_huggingface import HuggingFaceEmbeddings

def LoadModel(model_path='../../model/bge-large-zh-v1.5'):
    
    base_dir = os.getcwd()
    model_dir = load_nested_params("model","embedding","path")
    model_name = load_nested_params("model","embedding","name")
    if model_dir is None:
        model_path = model_name
    else:
        model_path = os.path.join(base_dir, model_dir, model_name)
    
    device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model_kwargs = {'device': device}
    encode_kwargs = {'normalize_embeddings': False}
    embeddings = HuggingFaceEmbeddings(model_name=model_path,
                                       model_kwargs=model_kwargs,
                                       encode_kwargs=encode_kwargs)
    print("加载embedding模型成功！")
    return embeddings



