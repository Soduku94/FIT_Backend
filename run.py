from app import create_app

app = create_app()

if __name__ == '__main__':
    # In ra danh sách các Route để kiểm tra URL
    with app.app_context():
        print("\n--- REGISTERED ENDPOINTS ---")
        for rule in app.url_map.iter_rules():
            print(f"Endpoint: {rule.endpoint:20} | URL: {rule}")
        print("----------------------------------------\n")

    # Cho phép truy cập từ mạng nội bộ (host='0.0.0.0') để test mobile
    app.run(debug=True, host='0.0.0.0', port=5000)