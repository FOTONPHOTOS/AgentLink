from ultralytics import YOLO
import os

MODEL_DIR = '/root/AgentLink/models'
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

print("🚀 Loading YOLOv8 Nano model...")
model = YOLO('yolov8n.pt')

print("📦 Exporting to ONNX format...")
# Export to ONNX
onnx_path = model.export(format='onnx', imgsz=640)

print(f" Model exported to: {onnx_path}")
