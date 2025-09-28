from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # se não estiver logado → redireciona
            if not current_user.is_authenticated:
                flash("Você precisa estar logado.", "warning")
                return redirect(url_for("login"))

            # se role for lista → permite múltiplos
            if isinstance(role, (list, tuple)):
                if current_user.tipo not in role:
                    flash("Acesso não permitido para o seu perfil.", "danger")
                    return redirect(url_for("login"))
            else:
                # se for string → verifica apenas um
                if current_user.tipo != role:
                    flash("Acesso não permitido para o seu perfil.", "danger")
                    return redirect(url_for("login"))

            return f(*args, **kwargs)
        return wrapper
    return decorator
