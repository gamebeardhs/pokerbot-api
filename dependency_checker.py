#!/usr/bin/env python3
"""
Dependency checker for poker advisory system.
Checks for required dependencies before installation.
"""

import sys
import subprocess
import importlib
from typing import Dict, List, Tuple, Optional

class DependencyChecker:
    """Smart dependency checker with version validation."""
    
    def __init__(self):
        self.required_deps = {
            # Core dependencies (always required)
            'core': [
                ('fastapi', '0.100.0'),
                ('uvicorn', '0.20.0'),
                ('pydantic', '2.0.0'),
                ('python-multipart', '0.0.6'),
                ('websockets', '11.0.0'),
                ('requests', '2.30.0')
            ],
            # Computer vision dependencies
            'vision': [
                ('opencv-python', '4.8.0'),
                ('pillow', '10.0.0'),
                ('numpy', '1.24.0'),
                ('pytesseract', '0.3.10'),
                ('mss', '9.0.0'),
                ('pyautogui', '0.9.54'),
                ('imagehash', '4.3.1')
            ],
            # Enhanced OCR (optional)
            'enhanced_ocr': [
                ('easyocr', '1.7.0')  # Optional - will gracefully degrade if unavailable
            ],
            # Machine learning (optional)
            'ml': [
                ('scikit-learn', '1.3.0'),
                ('pandas', '2.0.0'),
                ('joblib', '1.3.0'),
                ('hnswlib', '0.7.0')
            ],
            # Game theory (optional)
            'game_theory': [
                ('open-spiel', '1.3.0'),  # Optional - will use fallback if unavailable
                ('tensorflow', '2.13.0')  # Required by open-spiel
            ],
            # Development/testing
            'dev': [
                ('pytest', '7.4.0'),
                ('pytest-asyncio', '0.21.0')
            ],
            # Web scraping (optional)
            'scraping': [
                ('trafilatura', '1.6.0'),
                ('playwright', '1.40.0')
            ]
        }
    
    def check_package_installed(self, package_name: str) -> Tuple[bool, Optional[str]]:
        """Check if a package is installed and return version."""
        try:
            module = importlib.import_module(package_name.replace('-', '_'))
            version = getattr(module, '__version__', 'unknown')
            return True, version
        except ImportError:
            return False, None
    
    def check_system_requirements(self) -> Dict[str, any]:
        """Check system-level requirements."""
        results = {
            'python_version': sys.version,
            'python_compatible': sys.version_info >= (3, 8),
            'platform': sys.platform
        }
        
        # Check for Tesseract OCR
        try:
            result = subprocess.run(['tesseract', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            results['tesseract_available'] = result.returncode == 0
            if results['tesseract_available']:
                # Extract version from output
                version_line = result.stdout.split('\n')[0]
                results['tesseract_version'] = version_line
        except (subprocess.TimeoutExpired, FileNotFoundError):
            results['tesseract_available'] = False
            results['tesseract_version'] = None
        
        return results
    
    def check_dependencies(self, categories: List[str] = None) -> Dict[str, any]:
        """Check all dependencies in specified categories."""
        if categories is None:
            categories = ['core', 'vision']  # Essential categories only
        
        results = {
            'system': self.check_system_requirements(),
            'packages': {},
            'missing': [],
            'optional_missing': [],
            'summary': {}
        }
        
        total_required = 0
        total_installed = 0
        
        for category in categories:
            if category not in self.required_deps:
                continue
                
            results['packages'][category] = {}
            category_missing = []
            
            for package_name, min_version in self.required_deps[category]:
                total_required += 1
                is_installed, current_version = self.check_package_installed(package_name)
                
                results['packages'][category][package_name] = {
                    'installed': is_installed,
                    'current_version': current_version,
                    'required_version': min_version
                }
                
                if is_installed:
                    total_installed += 1
                else:
                    category_missing.append(package_name)
                    
                    # Categorize as optional or required
                    if category in ['enhanced_ocr', 'ml', 'game_theory', 'dev', 'scraping']:
                        results['optional_missing'].append(package_name)
                    else:
                        results['missing'].append(package_name)
        
        results['summary'] = {
            'total_required': total_required,
            'total_installed': total_installed,
            'install_percentage': (total_installed / total_required * 100) if total_required > 0 else 0,
            'critical_missing': len(results['missing']),
            'optional_missing': len(results['optional_missing'])
        }
        
        return results
    
    def generate_install_commands(self, missing_packages: List[str]) -> List[str]:
        """Generate pip install commands for missing packages."""
        if not missing_packages:
            return []
        
        # Group packages for efficient installation
        commands = []
        
        # Core packages first
        core_packages = []
        optional_packages = []
        
        for package in missing_packages:
            is_optional = False
            for category in ['enhanced_ocr', 'ml', 'game_theory', 'dev', 'scraping']:
                if any(pkg[0] == package for pkg in self.required_deps.get(category, [])):
                    optional_packages.append(package)
                    is_optional = True
                    break
            
            if not is_optional:
                core_packages.append(package)
        
        if core_packages:
            commands.append(f"pip install {' '.join(core_packages)}")
        
        if optional_packages:
            commands.append(f"# Optional packages (for enhanced features):")
            commands.append(f"pip install {' '.join(optional_packages)}")
        
        return commands
    
    def print_dependency_report(self, categories: List[str] = None):
        """Print a comprehensive dependency report."""
        results = self.check_dependencies(categories)
        
        print("🔍 POKER ADVISORY SYSTEM - DEPENDENCY CHECK")
        print("=" * 60)
        
        # System requirements
        sys_info = results['system']
        print(f"\n📋 SYSTEM REQUIREMENTS:")
        print(f"   Python Version: {sys_info['python_version'].split()[0]}")
        print(f"   Python Compatible: {'✅' if sys_info['python_compatible'] else '❌'}")
        print(f"   Platform: {sys_info['platform']}")
        print(f"   Tesseract OCR: {'✅' if sys_info['tesseract_available'] else '❌'}")
        
        # Package status
        print(f"\n📦 PACKAGE STATUS:")
        for category, packages in results['packages'].items():
            print(f"\n   {category.upper()}:")
            for pkg_name, pkg_info in packages.items():
                status = "✅" if pkg_info['installed'] else "❌"
                version_info = f"v{pkg_info['current_version']}" if pkg_info['installed'] else "not installed"
                print(f"     {status} {pkg_name}: {version_info}")
        
        # Summary
        summary = results['summary']
        print(f"\n📊 SUMMARY:")
        print(f"   Packages Installed: {summary['total_installed']}/{summary['total_required']} ({summary['install_percentage']:.1f}%)")
        print(f"   Critical Missing: {summary['critical_missing']}")
        print(f"   Optional Missing: {summary['optional_missing']}")
        
        # Installation commands
        if results['missing'] or results['optional_missing']:
            print(f"\n💾 INSTALLATION COMMANDS:")
            all_missing = results['missing'] + results['optional_missing']
            commands = self.generate_install_commands(all_missing)
            for cmd in commands:
                print(f"   {cmd}")
        
        # Overall status
        if summary['critical_missing'] == 0:
            print(f"\n🚀 STATUS: READY FOR DEPLOYMENT")
        else:
            print(f"\n⚠️  STATUS: MISSING CRITICAL DEPENDENCIES")
        
        return results

def main():
    """Main dependency check function."""
    checker = DependencyChecker()
    
    # Check core and vision dependencies (essential)
    print("Checking essential dependencies...")
    results = checker.print_dependency_report(['core', 'vision'])
    
    # Check optional dependencies
    print("\n" + "="*60)
    print("Checking optional dependencies...")
    optional_results = checker.print_dependency_report(['enhanced_ocr', 'ml', 'game_theory'])
    
    return results

if __name__ == "__main__":
    main()