from flask import redirect, url_for, flash, Blueprint
from ..rule_loader import load_rules
from ..update_rules import update_sigma_database
from ..config import ensure_rules_dir


def create_update_blueprint(rules):
    bp = Blueprint('update', __name__)

    @bp.route('/update', methods=['POST'])
    def update():
        try:
            rules_dir = ensure_rules_dir()
            update_sigma_database(rules_dir)
            new_rules = load_rules(rules_dir)
            rules.clear()
            rules.extend(new_rules)
            flash('Sigma rules updated successfully!', 'success')
        except Exception as e:
            flash(f'Update failed: {e}', 'danger')
        return redirect(url_for('main.index'))

    return bp


