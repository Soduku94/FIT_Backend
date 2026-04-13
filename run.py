from app import create_app

app = create_app()

if __name__ == '__main__':
    # In ra danh sách các Route để kiểm tra URL
    with app.app_context():
        print("\n--- DANH SÁCH CÁC ENDPOINT ĐÃ ĐĂNG KÝ ---")
        for rule in app.url_map.iter_rules():
            print(f"Endpoint: {rule.endpoint:20} | URL: {rule}")
        print("----------------------------------------\n")

    app.run(debug=True)