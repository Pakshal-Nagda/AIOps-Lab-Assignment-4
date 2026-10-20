import io, time, uuid, zipfile
import streamlit as st, torch
from PIL import Image, UnidentifiedImageError
from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server, disable_created_metrics
from transformers import BlipProcessor, BlipForConditionalGeneration

st.set_page_config(page_title="CPU Image Captioning", page_icon="🖼️", layout="wide")
st.title("CPU Image Captioning with Prometheus")
disable_created_metrics()

@st.cache_resource
def setup():
    m = {
        "images": Counter("images_processed", "Images processed", ["mode", "status", "session_id"]),
        "active": Gauge("active_requests", "Active requests"),
        "latency": Histogram("inference_latency_seconds", "Inference latency", ["mode"]),
        "summary": Summary("inference_latency_summary", "Inference latency", ["mode"])
    }
    try:
        start_http_server(8000)
        server = True
    except OSError:
        server = False
    p = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to("cpu").eval()
    return m, server, p, model

try:
    M, server, processor, model = setup()
except Exception as e:
    st.error(f"Model initialization failed: {e}")
    st.stop()

sid = st.session_state.setdefault("session_id", str(uuid.uuid4()))

def process(image, mode):
    start = time.perf_counter()
    M["active"].inc()
    try:
        with torch.inference_mode():
            inputs = processor(images=image.convert("RGB"), return_tensors="pt")
            return processor.decode(model.generate(**inputs)[0], skip_special_tokens=True)
    finally:
        duration = time.perf_counter() - start
        M["latency"].labels(mode).observe(duration)
        M["summary"].labels(mode).observe(duration)
        M["active"].dec()

def record(mode, status):
    M["images"].labels(mode, status, sid).inc()

mode = st.radio("Processing Mode", ["Single", "Bulk"], horizontal=True)

if mode == "Single":
    file = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])
    if file:
        try:
            image = Image.open(file).convert("RGB")
            st.image(image, width='content')
            if st.button("Generate Caption", type="primary"):
                try:
                    caption = process(image, mode)
                    record(mode, "success")
                    st.success(caption)
                except Exception as e:
                    record(mode, "failure")
                    st.error(str(e))
        except (UnidentifiedImageError, OSError, ValueError):
            st.error("Invalid image.")
else:
    file = st.file_uploader("Upload image ZIP", type="zip")
    if file and st.button("Process Batch", type="primary"):
        try:
            with zipfile.ZipFile(io.BytesIO(file.getvalue())) as z:
                files = [n for n in z.namelist() if not n.endswith("/") and n.lower().endswith((".png", ".jpg", ".jpeg"))]
                if not files:
                    st.warning("No supported images found.")
                else:
                    progress = st.progress(0)
                    success = failed = 0
                    for i, name in enumerate(files):
                        try:
                            with z.open(name) as f:
                                image = Image.open(io.BytesIO(f.read())).convert("RGB")
                            caption = process(image, mode)
                            record(mode, "success")
                            success += 1
                            st.write(f"**{name}:** {caption}")
                        except Exception as e:
                            record(mode, "failure")
                            failed += 1
                            st.warning(f"{name}: {e}")
                        progress.progress((i + 1) / len(files))
                    st.success(f"Complete: {success} successful, {failed} failed.")
        except zipfile.BadZipFile:
            st.error("Invalid ZIP file.")
        except Exception as e:
            st.error(str(e))
