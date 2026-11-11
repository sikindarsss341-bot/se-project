import requests

res = requests.get('http://127.0.0.1:8000/')
print('Status:', res.status_code)
views = [
    'view-dashboard',
    'view-image-detection',
    'view-video-detection',
    'view-live-monitoring',
    'view-analytics',
    'view-incident-history',
    'view-alerts',
    'view-reports',
    'view-model-info',
    'view-settings'
]
for v in views:
    found = f'id="{v}"' in res.text
    print(f"View {v}: {'FOUND' if found else 'MISSING'}")
print("Chart.js script:", "FOUND" if "chart.js" in res.text.lower() else "MISSING")
