# Define the base directory
$baseDir = ".\backend"

# Create main directory structure
$dirs = @(
    "app",
    "app\models",
    "app\services",
    "app\tasks",
    "app\api"
)

# Create directories
foreach ($dir in $dirs) {
    New-Item -Path "$baseDir\$dir" -ItemType Directory -Force
}

# Create empty Python files
$files = @(
    "app\__init__.py",
    "app\extensions.py",
    "app\models\__init__.py",
    "app\models\platform.py",
    "app\models\security.py",
    "app\models\transaction.py",
    "app\models\price_history.py",
    "app\models\holding.py",
    "app\models\dividend.py",
    "app\services\__init__.py",
    "app\services\price_service.py",
    "app\services\portfolio_service.py",
    "app\tasks\__init__.py",
    "app\tasks\celery_tasks.py",
    "app\api\__init__.py",
    "app\api\dashboard.py",
    "app\api\portfolio.py",
    "app\api\transactions.py",
    "config.py",
    "run.py",
    "wsgi.py"
)

# Create files
foreach ($file in $files) {
    New-Item -Path "$baseDir\$file" -ItemType File -Force
}

Write-Host "Project structure created successfully!"
Write-Host "Directory structure:"
Get-ChildItem -Path $baseDir -Recurse -Directory | Select-Object FullName