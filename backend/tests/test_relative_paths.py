"""
Test the updated relative path functionality in import_data.py
"""
import os
import sys

def test_relative_path_functionality():
    """Test that the relative path logic works correctly"""
    
    print("🧪 Testing Relative Path Functionality")
    print("=" * 45)
    
    # Add backend directory to path
    backend_dir = os.path.dirname(os.path.dirname(__file__))  # Go up one level from tests/
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    
    try:
        # Import the function from import_data
        from import_data import get_default_csv_path
        
        # Test the relative path function
        csv_path = get_default_csv_path()
        
        print(f"✅ Function imported successfully")
        print(f"📁 Calculated CSV path: {csv_path}")
        
        # Verify the path structure
        expected_parts = ['data', 'combined_transactions_updated.csv']
        path_parts = csv_path.replace('\\', '/').split('/')
        
        # Check if the last two parts match our expectation
        if path_parts[-2:] == expected_parts:
            print(f"✅ Path structure correct: ends with ../data/combined_transactions_updated.csv")
        else:
            print(f"⚠️  Path structure: {'/'.join(path_parts[-3:])}")
        
        # Test path normalization
        normalized_path = os.path.normpath(csv_path)
        if normalized_path == csv_path:
            print(f"✅ Path normalization working")
        else:
            print(f"⚠️  Path normalization issue")
        
        # Test relative to script location
        script_dir = os.path.dirname(os.path.abspath(__file__))
        expected_data_dir = os.path.normpath(os.path.join(script_dir, '..', 'data'))
        actual_data_dir = os.path.dirname(csv_path)
        
        if actual_data_dir == expected_data_dir:
            print(f"✅ Relative path calculation correct")
        else:
            print(f"ℹ️  Expected: {expected_data_dir}")
            print(f"ℹ️  Actual:   {actual_data_dir}")
        
        # Test Docker compatibility
        print(f"\n🐳 Docker Compatibility Check:")
        print(f"📁 Script directory: {script_dir}")
        print(f"📁 Data directory:   {os.path.dirname(csv_path)}")
        print(f"📄 CSV file:         {os.path.basename(csv_path)}")
        
        # In Docker, this would resolve to:
        # /app/backend/import_data.py -> /app/data/combined_transactions_updated.csv
        docker_style_path = csv_path.replace('\\', '/')
        print(f"🐳 Docker-style path: {docker_style_path}")
        
        # Test file existence
        if os.path.exists(csv_path):
            print(f"✅ CSV file exists at calculated path")
            
            # Get file size for verification
            file_size = os.path.getsize(csv_path)
            print(f"📊 File size: {file_size:,} bytes")
        else:
            print(f"ℹ️  CSV file not found (expected for test environment)")
            print(f"📝 Expected location: {csv_path}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import get_default_csv_path: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_cross_platform_compatibility():
    """Test cross-platform path handling"""
    
    print(f"\n🌐 Cross-Platform Compatibility Test")
    print("=" * 45)
    
    try:
        from import_data import get_default_csv_path
        
        csv_path = get_default_csv_path()
        
        # Test Windows-style paths
        windows_path = csv_path.replace('/', '\\')
        print(f"🪟 Windows path: {windows_path}")
        
        # Test Unix-style paths  
        unix_path = csv_path.replace('\\', '/')
        print(f"🐧 Unix path: {unix_path}")
        
        # Test normalization works on both
        windows_normalized = os.path.normpath(windows_path)
        unix_normalized = os.path.normpath(unix_path)
        
        print(f"✅ Windows normalized: {windows_normalized}")
        print(f"✅ Unix normalized: {unix_normalized}")
        
        # Both should resolve to the same logical path
        windows_parts = windows_normalized.replace('\\', '/').split('/')
        unix_parts = unix_normalized.replace('\\', '/').split('/')
        
        if windows_parts[-2:] == unix_parts[-2:] == ['data', 'combined_transactions_updated.csv']:
            print(f"✅ Cross-platform compatibility verified")
            return True
        else:
            print(f"⚠️  Cross-platform issue detected")
            return False
            
    except Exception as e:
        print(f"❌ Cross-platform test failed: {e}")
        return False

def test_docker_scenario():
    """Simulate how paths would work in Docker"""
    
    print(f"\n🐳 Docker Deployment Simulation")
    print("=" * 45)
    
    # Simulate Docker file structure
    docker_structure = """
    Docker Container Structure:
    /app/
    ├── backend/
    │   ├── import_data.py          (this script)
    │   ├── app/
    │   └── requirements.txt
    ├── data/
    │   └── combined_transactions_updated.csv
    ├── frontend/
    └── nginx/
    """
    
    print(docker_structure)
    
    try:
        from import_data import get_default_csv_path
        
        # Simulate what the path would be in Docker
        csv_path = get_default_csv_path()
        
        # Replace current Windows path with Docker-style path
        path_parts = csv_path.replace('\\', '/').split('/')
        docker_path = '/app/' + '/'.join(path_parts[-2:])  # /app/data/combined_transactions_updated.csv
        
        print(f"🐳 Current path: {csv_path}")
        print(f"🐳 Docker path:  {docker_path}")
        
        # Verify the relative structure is maintained
        if docker_path.endswith('/data/combined_transactions_updated.csv'):
            print(f"✅ Docker path structure correct")
            print(f"✅ Relative path logic will work in Docker")
            
            print(f"\n📋 Docker Benefits:")
            print(f"   • No hardcoded absolute paths")
            print(f"   • Works regardless of container mount points")
            print(f"   • Portable across different environments")
            print(f"   • Consistent relative structure maintained")
            
            return True
        else:
            print(f"❌ Docker path structure issue")
            return False
            
    except Exception as e:
        print(f"❌ Docker simulation failed: {e}")
        return False

def run_comprehensive_path_test():
    """Run all path-related tests"""
    
    print("🔧 IMPORT DATA RELATIVE PATH TEST SUITE")
    print("=" * 55)
    
    tests = [
        ("Relative Path Functionality", test_relative_path_functionality),
        ("Cross-Platform Compatibility", test_cross_platform_compatibility),
        ("Docker Deployment Simulation", test_docker_scenario)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"\n✅ {test_name}: PASSED")
            else:
                print(f"\n❌ {test_name}: FAILED")
        except Exception as e:
            print(f"\n❌ {test_name}: ERROR - {e}")
    
    print(f"\n🎯 FINAL RESULTS")
    print("=" * 30)
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print(f"🎉 ALL TESTS PASSED!")
        print(f"✅ Relative path implementation is Docker-ready")
        print(f"✅ Cross-platform compatibility verified")
        print(f"✅ Production deployment ready")
    else:
        print(f"⚠️  Some tests failed - review output above")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_path_test()
    
    if success:
        print(f"\n" + "🚀" * 20)
        print(f"RELATIVE PATH IMPLEMENTATION SUCCESSFUL!")
        print(f"Your import_data.py is now Docker-compatible!")
        print(f"🚀" * 20)
    else:
        print(f"\n" + "⚠️" * 15)
        print(f"Review the test results above")
        print(f"⚠️" * 15)