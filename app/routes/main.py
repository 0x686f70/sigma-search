from flask import render_template, request, Blueprint, current_app, send_file, make_response, Response
from ..rule_loader import search_rules
from ..advanced_search import search_rules_advanced
from ..rule_processor import group_and_sort_rules
import os


def create_main_blueprint(rules):
    bp = Blueprint('main', __name__)

    @bp.route('/favicon.ico')
    def favicon():
        svg_inline = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="l" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#90CAF9"/>
      <stop offset="1" stop-color="#42A5F5"/>
    </linearGradient>
    <linearGradient id="r" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#64B5F6"/>
      <stop offset="1" stop-color="#1E88E5"/>
    </linearGradient>
  </defs>
  <path d="M256 32L64 96v144c0 130.9 84.4 251.3 192 288 107.6-36.7 192-157.1 192-288V96L256 32z" fill="#0B3D91"/>
  <path d="M256 48L80 106v134c0 121.5 76.9 232.5 176 266V48z" fill="url(#l)"/>
  <path d="M256 48v458c99.1-33.5 176-144.5 176-266V106L256 48z" fill="url(#r)"/>
</svg>
    """
        resp = make_response(Response(svg_inline, mimetype='image/svg+xml'))
        resp.headers['Cache-Control'] = 'public, max-age=604800, immutable'
        return resp

    @bp.route('/', methods=['GET', 'POST'])
    def index():
        results = []
        query = ''
        category = request.args.get('category', '').strip()
        subcategory = request.args.get('subcategory', '').strip()
        deployment_status = request.args.get('deployment_status', '').strip()
        grouped_rules = None
        filter_description = []

        # Start with all rules
        results = rules.copy()

        # Filter by deployment status
        if deployment_status in ['deployed', 'undeployed']:
            deployment_manager = current_app.deployment_manager
            deployed_rules = set(deployment_manager.get_deployed_rules())
            
            if deployment_status == 'deployed':
                results = [r for r in results if r['file_path'] in deployed_rules]
                filter_description.append('Deployed')
            elif deployment_status == 'undeployed':
                results = [r for r in results if r['file_path'] not in deployed_rules]
                filter_description.append('Undeployed')

        # Filter by category and subcategory
        if category:
            results = [r for r in results if category.lower() in r['file_path'].lower().split('/')]
            filter_description.append(category.capitalize())
            if subcategory:
                results = [r for r in results if subcategory.lower() in r['file_path'].lower().split('/')]
                filter_description.append(subcategory.replace('_', ' ').capitalize())

        # Apply search query if it exists
        if request.method == 'POST':
            query = request.form.get('query', '').strip()
        else:
            query = request.args.get('query', '').strip()

        if query:
            results = search_rules_advanced(results, query)  # Advanced search within filtered results

        # Create descriptive text for the filtered/searched results
        result_description = ''
        if filter_description:
            result_description = f" in {' > '.join(filter_description)}"
        if query:
            result_description = f" for \"{query}\"" + result_description

        if results:
            # Pass the category to group_and_sort_rules when filtering
            grouped_rules = group_and_sort_rules(results, category if category else None)

        return render_template('index.html', 
                            results=results, 
                            query=query, 
                            grouped_rules=grouped_rules,
                            selected_category=category,
                            selected_subcategory=subcategory,
                            selected_deployment_status=deployment_status,
                            result_description=result_description)

    return bp


