from normalize import normalize_posting

sample_job = {
    'category': {'tag': 'it-jobs', 'label': 'IT Jobs'},
    'salary_is_predicted': '0',
    'created': '2026-06-18T21:48:12Z',
    'title': 'Manager, Client Success Business Consulting',
    'redirect_url': 'https://www.adzuna.in/land/ad/5768228434',
    'id': '5768228434',
    'company': {'display_name': 'Concentrix'},
    'description': 'Experience: 6 Years Job Summary...',
    'location': {'area': ['India', 'Karnataka', 'Bangalore'], 'display_name': 'Bangalore, Karnataka'}
}

cleaned = normalize_posting(sample_job)
print(cleaned)