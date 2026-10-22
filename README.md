# DA3408 AIOps Lab - Assignment 4

## Instructions for running the code

### Setup
1. Install required packages
    ```
    pip install -r requirements.txt
    ```
2. Download Prometheus and Node Exporter from [here](https://prometheus.io/download/) and extract the executables.
    ```
    tar -xzf prometheus-3.15.0.linux-amd64.tar.gz       # Replace the version number appropriately
    tar -xzf node_exporter-1.12.1.linux-amd64.tar.gz    # Replace the version number appropriately
    ```
3. Set up a docker container for grafana
    ```
    docker pull grafana/grafana-enterprise
    docker run -d -p 3000:3000 --name=grafana grafana/grafana-enterprise
    ```
4. Run the following command to know your ip address
    ```
    ip address
    ```

### App testing
1. In a separate terminal, in the directory containing `node_exporter`, run
    ```
    ./node_exporter
    ```
    The node exporter will start at port 9100 by default.
2. In a separate terminal, in the directory containing `prometheus`, replace `prometheus.yml` with the `prometheus.yml` from this repository and run
    ```
    ./prometheus
    ```
3. Start the streamlit app using
    ```
    streamlit run app.py
    ```
    It will open a page on port 8501 by default. Interact with the page a few times.
4. Go to `http://localhost:9090` to inspect metrics using PromQL.
5. To inspect metrics using Grafana, run
    ```
    docker start grafana
    ```
    Go to `http://localhost:3000` to view the Grafana UI. The username and password is `admin` by default.  
    Go to Connections --> Add new connection --> Prometheus --> Add new data source.  
    Enter the Prometheus server URL as `http://<YOUR-IP-ADDRESS>:9090` and click Save & Test.  
    Once Grafana shows success message, click on the + icon on the top right corner of the screen and select Import dashboard.  
    Upload `dashboard.json` and click Import. The dashboard is now visible and reflects the metrics from the application.
6. Interact with the application manually or use the automatic script using
    ```
    python dummy_requests.py
    ```
    and inspect the change in metrics on the Grafana dashboard.

## Reference for evaluation (For TAs)

1. **Python Instrumentation**: `app.py` contains the code powering the main image captioning app. It uses Counters, Gauges, Summary, Histograms and labels for client tracking effectively.
    - Counter - `images_processed` - Images processed by the application
    - Gauge - `active_requests` - Active requests being handled by the application
    - Histogram - `inference_latency_seconds` - Latency incurred during inference
    - Summary - `inference_latency_summary` - Summary of inference latency
    - Custom labels like `session_id`, `status` and `mode` are also tracked by the above objects, allowing to group the data efficiently on the dashboard.
2. **Node Exporting**: `prometheus.yml` contains a minimal config for Prometheus that intergrates both node exporter metrics and metrics from the streamlit app.
3. **Grafana Intuitiveness**: Run the steps mentioned in the above section to get the app and Grafana dashboard running. Use the `dashboard.json` to get the live plots to evaluate them on the basis of plotting commandments. The dashboard includes Current App Status, Number of active requests being processed, Throughput, Latency and CPU Usage.
4. **Application Logic**: The streamlit app loads the model once and stores it in cache to avoid redundant model loading costs for every image. It can handle single and multiple image uploads without crashing. In the rare event that it is not able to store all of the images in the memory together, it gracefully throws an error without crashing.

Apart from the above, the video recording of the entire working demo is available [here](https://drive.google.com/file/d/1yxwfo75Z38obg1U4tbiEB2DvJO2-u_IV/view)

## LLM Usage Disclosure
Gemini was used to write the code for `app.py` and `dummy_requests.py` since I did not know the syntax and working of streamlit.  
ChatGPT was used often to refine my understanding of Prometheus and Grafana and to resolve minor bugs.