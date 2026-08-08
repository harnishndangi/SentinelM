def test_get_models_and_fraud_detector(client):
    # Test GET /api/v1/models
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    models = response.json()
    assert isinstance(models, list)
    model_names = [m["name"] for m in models]
    assert "FraudDetector" in model_names

    # Test GET /api/v1/models/FraudDetector
    response = client.get("/api/v1/models/FraudDetector")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "FraudDetector"
    assert data["production_version"] == "1"
    
    metric_map = {m["name"]: m["value"] for m in data["metrics"]}
    assert metric_map.get("precision") == 0.92
    assert metric_map.get("recall") == 0.93
    assert metric_map.get("f1") == 0.91
    assert metric_map.get("roc_auc") == 0.97
    assert metric_map.get("pr_auc") == 0.94
