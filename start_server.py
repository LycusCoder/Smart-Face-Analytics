#!/usr/bin/env python3
"""
Smart Face Analytics - Auto Start Server Script
Script untuk menjalankan backend dan frontend secara otomatis
"""

import os
import sys
import subprocess
import time
import signal
import threading
import importlib.util
from pathlib import Path

class ServerManager:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.base_dir = Path(__file__).parent.absolute()
        
    def print_banner(self):
        """Print aplikasi banner"""
        banner = """
╔════════════════════════════════════════════════════════════════╗
║                   🧠 SMART FACE ANALYTICS                     ║
║                Auto Server Starter Script                     ║
╚════════════════════════════════════════════════════════════════╝
        """
        print(banner)
        
    def check_prerequisites(self):
        """Check semua prerequisites terpenuhi"""
        print("🔍 Checking prerequisites...")
        
        # Check Python version
        try:
            python_version = subprocess.check_output([sys.executable, '--version']).decode().strip()
            print(f"✅ {python_version}")
        except:
            print("❌ Python tidak terinstall")
            return False
            
        # Check Node.js
        try:
            node_version = subprocess.check_output(['node', '--version']).decode().strip()
            print(f"✅ {node_version}")
        except:
            print("❌ Node.js tidak terinstall")
            return False
            
        # Check Yarn
        try:
            yarn_version = subprocess.check_output(['yarn', '--version']).decode().strip()
            print(f"✅ Yarn {yarn_version}")
        except:
            print("❌ Yarn tidak terinstall")
            return False
            
        # Check directory structure
        required_dirs = ['backend', 'frontend']
        for dir_name in required_dirs:
            if (self.base_dir / dir_name).exists():
                print(f"✅ Directory '{dir_name}' ditemukan")
            else:
                print(f"❌ Directory '{dir_name}' tidak ditemukan")
                return False
                
        print("✅ Semua prerequisites terpenuhi!")
        return True

    def check_python_package_installed(self, package_name):
        """Check jika Python package sudah terinstall"""
        try:
            spec = importlib.util.find_spec(package_name)
            return spec is not None
        except ImportError:
            return False

    def get_required_packages(self):
        """Dapatkan list package dari requirements.txt"""
        backend_dir = self.base_dir / "backend"
        requirements_file = backend_dir / "requirements.txt"
        
        if not requirements_file.exists():
            return []
            
        with open(requirements_file, 'r', encoding='utf-8') as f:
            packages = []
            for line in f:
                line = line.strip()
                # Skip empty lines dan comments
                if not line or line.startswith('#') or line.startswith('--'):
                    continue
                # Extract package name (remove version specifiers)
                package_name = line.split('>=')[0].split('==')[0].split('[')[0].strip()
                if package_name:
                    packages.append(package_name)
            return packages

    def check_backend_dependencies(self):
        """Check apakah semua backend dependencies sudah terinstall"""
        print("🔍 Checking backend dependencies...")
        
        backend_dir = self.base_dir / "backend"
        requirements_file = backend_dir / "requirements.txt"
        
        if not requirements_file.exists():
            print("❌ requirements.txt tidak ditemukan")
            return False
            
        required_packages = self.get_required_packages()
        missing_packages = []
        
        for package in required_packages:
            if self.check_python_package_installed(package):
                print(f"  ✅ {package}")
            else:
                print(f"  ❌ {package}")
                missing_packages.append(package)
                
        if missing_packages:
            print(f"📦 {len(missing_packages)} packages perlu diinstall")
            return False
        else:
            print("✅ Semua backend dependencies sudah terinstall")
            return True

    def check_frontend_dependencies(self):
        """Check apakah frontend dependencies sudah terinstall"""
        print("🔍 Checking frontend dependencies...")
        
        frontend_dir = self.base_dir / "frontend"
        node_modules = frontend_dir / "node_modules"
        package_json = frontend_dir / "package.json"
        
        if not package_json.exists():
            print("❌ package.json tidak ditemukan")
            return False
            
        if node_modules.exists():
            # Check jika node_modules ada dan tidak kosong
            try:
                list_dir = list(node_modules.iterdir())
                if len(list_dir) > 0:
                    print("✅ Frontend dependencies sudah terinstall")
                    return True
                else:
                    print("❌ node_modules kosong")
                    return False
            except OSError:
                print("❌ Tidak bisa akses node_modules")
                return False
        else:
            print("❌ node_modules tidak ditemukan")
            return False

    def install_backend_dependencies(self):
        """Install backend dependencies hanya jika diperlukan"""
        print("🔧 Checking backend dependencies...")
        
        if self.check_backend_dependencies():
            print("✅ Backend dependencies sudah up-to-date")
            return True
            
        print("📦 Installing missing backend dependencies...")
        backend_dir = self.base_dir / "backend"
        
        try:
            # Gunakan pip install dengan upgrade strategy
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt",
                "--upgrade", "--quiet"
            ], cwd=backend_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Backend dependencies installed/updated")
                return True
            else:
                print(f"❌ Gagal install backend dependencies: {result.stderr}")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Gagal install backend dependencies: {e}")
            return False

    def install_frontend_dependencies(self):
        """Install frontend dependencies hanya jika diperlukan"""
        print("🔧 Checking frontend dependencies...")
        
        if self.check_frontend_dependencies():
            print("✅ Frontend dependencies sudah up-to-date")
            return True
            
        print("📦 Installing frontend dependencies...")
        frontend_dir = self.base_dir / "frontend"
        
        try:
            # Check jika yarn.lock ada untuk menentukan install strategy
            yarn_lock = frontend_dir / "yarn.lock"
            if yarn_lock.exists():
                # Jika yarn.lock ada, gunakan yarn install (deterministic)
                result = subprocess.run(["yarn", "install", "--silent"], 
                                      cwd=frontend_dir, capture_output=True, text=True)
            else:
                # Jika tidak, gunakan yarn untuk install biasa
                result = subprocess.run(["yarn", "install", "--silent"], 
                                      cwd=frontend_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Frontend dependencies installed")
                return True
            else:
                print(f"❌ Gagal install frontend dependencies: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Gagal install frontend dependencies: {e}")
            return False

    def install_dependencies(self):
        """Install dependencies hanya jika diperlukan"""
        print("\n📦 Checking dependencies...")
        
        backend_success = self.install_backend_dependencies()
        frontend_success = self.install_frontend_dependencies()
        
        return backend_success and frontend_success

    def check_environment_files(self):
        """Check dan setup environment files"""
        print("\n🔧 Checking environment files...")
        
        # Backend environment
        backend_dir = self.base_dir / "backend"
        backend_env = backend_dir / ".env"
        backend_env_example = backend_dir / ".env.example"
        
        if not backend_env.exists() and backend_env_example.exists():
            print("📝 Creating backend .env file from .env.example")
            backend_env.write_text(backend_env_example.read_text())
            print("✅ Backend .env file created")
        elif backend_env.exists():
            print("✅ Backend .env file already exists")
        else:
            print("⚠️  Backend .env.example not found")
            
        # Frontend environment
        frontend_dir = self.base_dir / "frontend"
        frontend_env = frontend_dir / ".env"
        frontend_env_example = frontend_dir / ".env.example"
        
        if not frontend_env.exists() and frontend_env_example.exists():
            print("📝 Creating frontend .env file from .env.example")
            env_content = frontend_env_example.read_text()
            # Ensure backend URL is correct
            if "REACT_APP_BACKEND_URL" not in env_content:
                env_content += "\nREACT_APP_BACKEND_URL=http://localhost:8001"
            frontend_env.write_text(env_content)
            print("✅ Frontend .env file created")
        elif frontend_env.exists():
            print("✅ Frontend .env file already exists")
        else:
            print("⚠️  Frontend .env.example not found")

    def start_backend(self):
        """Start backend server"""
        print("\n🔧 Starting backend server...")
        backend_dir = self.base_dir / "backend"
            
        try:
            # Start backend server
            self.backend_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", "server:app", 
                "--host", "0.0.0.0", "--port", "8001", "--reload"
            ], cwd=backend_dir)
            
            print("✅ Backend server started on http://localhost:8001")
            return True
            
        except Exception as e:
            print(f"❌ Gagal start backend server: {e}")
            return False
            
    def start_frontend(self):
        """Start frontend development server"""
        print("\n🎨 Starting frontend server...")
        frontend_dir = self.base_dir / "frontend"
            
        try:
            # Start frontend server
            self.frontend_process = subprocess.Popen([
                "yarn", "start"
            ], cwd=frontend_dir)
            
            print("✅ Frontend server started on http://localhost:3000")
            return True
            
        except Exception as e:
            print(f"❌ Gagal start frontend server: {e}")
            return False
            
    def wait_for_backend(self, timeout=30):
        """Wait for backend to be ready"""
        print("⏳ Waiting for backend to be ready...")
        import requests
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get("http://localhost:8001/api/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Backend is ready!")
                    return True
            except:
                pass
            time.sleep(2)
            
        print("⚠️  Backend lambat loading, melanjutkan...")
        return True  # Return True untuk melanjutkan meskipun timeout
        
    def monitor_processes(self):
        """Monitor processes and restart if needed"""
        def monitor():
            while True:
                if self.backend_process and self.backend_process.poll() is not None:
                    print("❌ Backend process stopped, restarting...")
                    self.start_backend()
                    
                if self.frontend_process and self.frontend_process.poll() is not None:
                    print("❌ Frontend process stopped, restarting...")
                    self.start_frontend()
                    
                time.sleep(5)
                
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        
    def signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        print("\n\n🛑 Shutting down servers...")
        
        if self.frontend_process:
            print("Stopping frontend server...")
            self.frontend_process.terminate()
            
        if self.backend_process:
            print("Stopping backend server...")
            self.backend_process.terminate()
            
        # Wait for processes to terminate
        time.sleep(2)
        
        # Force kill if still running
        if self.frontend_process and self.frontend_process.poll() is None:
            self.frontend_process.kill()
        if self.backend_process and self.backend_process.poll() is None:
            self.backend_process.kill()
            
        print("✅ All servers stopped. Goodbye! 👋")
        sys.exit(0)
        
    def run(self):
        """Main execution method"""
        self.print_banner()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("\n❌ Prerequisites tidak terpenuhi. Silakan install yang diperlukan.")
            sys.exit(1)
            
        # Setup environment files
        self.check_environment_files()
            
        # Install dependencies hanya jika diperlukan
        if not self.install_dependencies():
            print("\n⚠️  Ada masalah dengan dependencies, melanjutkan...")
            
        # Start servers
        if not self.start_backend():
            print("\n❌ Gagal start backend server.")
            sys.exit(1)
            
        # Wait for backend to be ready
        if not self.wait_for_backend():
            print("\n⚠️  Backend lambat loading, melanjutkan...")
            
        if not self.start_frontend():
            print("\n❌ Gagal start frontend server.")
            self.signal_handler(None, None)
            sys.exit(1)
            
        # Start process monitoring
        self.monitor_processes()
        
        print("\n" + "="*60)
        print("🎉 SMART FACE ANALYTICS BERHASIL DIAKTIFKAN!")
        print("="*60)
        print("🌐 Frontend: http://localhost:3000")
        print("🔧 Backend:  http://localhost:8001")
        print("📚 API Docs: http://localhost:8001/docs")
        print("⏹️  Press Ctrl+C to stop all servers")
        print("="*60)
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.signal_handler(None, None)

if __name__ == "__main__":
    manager = ServerManager()
    manager.run()