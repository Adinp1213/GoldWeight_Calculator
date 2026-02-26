from django.shortcuts import render
from django.http import HttpResponse
import pandas as pd
import io


# Mapping the conversion chart as a constant
KT_CONVERSION_FACTORS = {
    ('14kt', '18kt'): 1.282, ('14kt', '9kt'): 0.641,
    ('18kt', '14kt'): 0.78,  ('18kt', '9kt'): 0.5,
    ('9kt', '14kt'): 1.56,  ('9kt', '18kt'): 2.0,
    ('14kt', '14kt'): 1.0,   ('18kt', '18kt'): 1.0, ('9kt', '9kt'): 1.0
}

def calculator(request):
    """
    Handles both displaying the calculator form (GET) and processing
    the weight calculation (POST).
    """
    context = {}
    if request.method == "POST":
        try:
            # Inputs
            orig_wt = float(request.POST.get('orig_wt', 0))
            orig_sz = float(request.POST.get('orig_sz', 0))
            new_sz = float(request.POST.get('new_sz', 0))
            orig_kt = request.POST.get('orig_kt', '14kt')
            new_kt = request.POST.get('new_kt', '14kt')

            # Calculations
            size_factor = 1 + ((new_sz - orig_sz) * 0.02)
            kt_factor = KT_CONVERSION_FACTORS.get((orig_kt, new_kt), 1.0)
            
            # Final Output
            final_weight = orig_wt * kt_factor * size_factor

            context = {
                'sku': request.POST.get('sku'),
                'size_factor': round(size_factor, 4),
                'kt_factor': kt_factor,
                'final_weight': round(final_weight, 3),
                'submitted_data': request.POST # To repopulate form
            }
        except ValueError:
            context['error'] = "Please enter valid numeric values."

    return render(request, 'calculator.html', context)

def bulk_calculator(request):
    """
    Renders the bulk upload page.
    """
    return render(request, 'bulk_calculator.html')

def download_template(request):
    """
    Generates and serves a downloadable Excel template for bulk calculations.
    """
    # Define sample data
    data = {
        'SKU': ['SAMPLE-RING-01'],
        'Original Gold Weight': [5.0],
        'Original Size': [7],
        'Changed Size': [8],
        'Original Carat': ['14kt'],
        'Changed Carat': ['18kt']
    }
    df = pd.DataFrame(data)

    # Create an in-memory Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Bulk_Template')
    
    # Set the appropriate HTTP response headers for file download
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="bulk_upload_template.xlsx"'
    return response

def process_bulk_file(request):
    """
    Processes the uploaded Excel/CSV file, calculates new weights,
    and returns the results as a downloadable Excel file.
    """
    if request.method == 'POST' and request.FILES.get('bulk_file'):
        bulk_file = request.FILES['bulk_file']
        
        try:
            # Read the uploaded file into a pandas DataFrame
            if bulk_file.name.endswith('.csv'):
                df = pd.read_csv(bulk_file)
            else:
                df = pd.read_excel(bulk_file)

            # Function to apply the calculation to each row
            def calculate_row(row):
                orig_wt = float(row['Original Gold Weight'])
                orig_sz = float(row['Original Size'])
                new_sz = float(row['Changed Size'])
                orig_kt = str(row['Original Carat']).strip()
                new_kt = str(row['Changed Carat']).strip()

                size_factor = 1 + ((new_sz - orig_sz) * 0.02)
                kt_factor = KT_CONVERSION_FACTORS.get((orig_kt, new_kt), 1.0)
                
                final_weight = orig_wt * kt_factor * size_factor
                return round(final_weight, 3)

            # Apply the calculation and create a new column
            df['Increased Gold Weight'] = df.apply(calculate_row, axis=1)

            # Create an in-memory Excel file for the output
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Calculated_Weights')

            response = HttpResponse(
                output.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="calculated_weights.xlsx"'
            return response

        except Exception as e:
            return render(request, 'bulk_calculator.html', {'error': f"An error occurred: {e}"})

    return render(request, 'bulk_calculator.html', {'error': 'No file was uploaded.'})