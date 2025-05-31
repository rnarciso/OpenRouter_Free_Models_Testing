from app import app
import os

def test_app_structure():
    """Test that the Flask app structure is correct"""
    results = []
    
    # Test Flask app initialization
    results.append(f"Flask app initialized: {app is not None}")
    
    # Test routes
    routes = [str(rule) for rule in app.url_map.iter_rules()]
    results.append(f"Routes: {routes}")
    
    # Test directory structure
    dirs_to_check = ['templates', 'static', 'static/css', 'static/js', 'static/img']
    for dir_name in dirs_to_check:
        results.append(f"Directory '{dir_name}' exists: {os.path.isdir(dir_name)}")
    
    # Test files
    files_to_check = [
        'app.py',
        'templates/index.html',
        'static/css/style.css',
        'static/js/main.js'
    ]
    for file_name in files_to_check:
        results.append(f"File '{file_name}' exists: {os.path.isfile(file_name)}")
    
    return results

if __name__ == "__main__":
    results = test_app_structure()
    for result in results:
        print(result)
    
    print("\nAll tests completed. If all results are True, the Flask app structure is correct.")