# ═══════════════════════════════════════════════════════════════════════════════
# VoteStack3 — app.py patches for cohort voting flow
#
# Apply these changes to your existing app.py.
# Sections marked REPLACE show the old code → new code.
# Sections marked ADD show new code to insert.
# ═══════════════════════════════════════════════════════════════════════════════


# ── HELPER: add this near the other helpers (alongside load_role) ──────────────

def load_voting_status():
    """Return 'open' or 'closed' (defaults to 'closed' if not set)."""
    conn = get_db()
    row = conn.execute(
        "SELECT value FROM settings WHERE key='voting_status'"
    ).fetchone()
    conn.close()
    return row['value'] if row else 'closed'


# ── REPLACE: /vote route ────────────────────────────────────────────────────────
# OLD:
# @app.route('/vote')
# def vote():
#     if 'username' not in session:
#         return redirect(url_for('index'))
#     role = load_role()
#     conn = get_db()
#     rows = conn.execute("SELECT choice FROM choices WHERE role=?", (role,)).fetchall() if role else []
#     conn.close()
#     choices = [r['choice'] for r in rows]
#     if not role or not choices:
#         return "No role or choices available to vote on."
#     return render_template('vote.html', role=role, choices=choices)

# NEW:
@app.route('/vote')
def vote():
    if 'username' not in session:
        return redirect(url_for('index'))

    role   = load_role()
    status = load_voting_status()

    conn = get_db()
    rows = conn.execute(
        "SELECT choice FROM choices WHERE role=?", (role,)
    ).fetchall() if role else []

    has_voted = False
    tally     = {}
    if role:
        existing = conn.execute(
            "SELECT id FROM votes WHERE username=? AND role=?",
            (session['username'], role)
        ).fetchone()
        has_voted = existing is not None

        if status == 'closed':
            tally_rows = conn.execute(
                "SELECT choice, COUNT(*) as cnt FROM votes WHERE role=? GROUP BY choice",
                (role,)
            ).fetchall()
            tally = {r['choice']: r['cnt'] for r in tally_rows}

    conn.close()
    choices = [r['choice'] for r in rows]

    return render_template(
        'vote.html',
        role=role,
        status=status,
        choices=choices,
        has_voted=has_voted,
        tally=tally,
    )


# ── ADD: /toggle_voting route ───────────────────────────────────────────────────
# Add this anywhere near the other admin routes (e.g. after /update_choices)

@app.route('/toggle_voting', methods=['POST'])
def toggle_voting():
    if not admin_required():
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('index'))

    current = load_voting_status()
    new_status = 'closed' if current == 'open' else 'open'

    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES ('voting_status', ?)",
        (new_status,)
    )
    conn.commit()
    conn.close()

    if new_status == 'open':
        flash("Voting is now open. Voters can cast their ballots.", "success")
    else:
        flash("Voting is now closed. Tally is visible to voters.", "success")

    return redirect(url_for('admin_dashboard'))


# ── REPLACE: /admin_dashboard route ────────────────────────────────────────────
# OLD:
# @app.route('/admin_dashboard', methods=['GET'])
# def admin_dashboard():
#     if not admin_required():
#         flash("Access restricted to admin only.", "danger")
#         return redirect(url_for('index'))
#     role = load_role()
#     return render_template('admin_dashboard.html', role=role)

# NEW:
@app.route('/admin_dashboard', methods=['GET'])
def admin_dashboard():
    if not admin_required():
        flash("Access restricted to admin only.", "danger")
        return redirect(url_for('index'))
    role        = load_role()
    voting_open = load_voting_status() == 'open'
    return render_template('admin_dashboard.html', role=role, voting_open=voting_open)


# ── REPLACE: /api/voter_status endpoint (replaces the one from previous patch) ──

@app.route('/api/voter_status', methods=['GET'])
def voter_status():
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 401

    role   = load_role()
    status = load_voting_status()

    if not role:
        return jsonify({"role": None, "status": "closed", "choices": [], "has_voted": False, "tally": {}})

    conn = get_db()
    rows = conn.execute(
        "SELECT choice FROM choices WHERE role=?", (role,)
    ).fetchall()
    existing = conn.execute(
        "SELECT id FROM votes WHERE username=? AND role=?",
        (session['username'], role)
    ).fetchone()

    tally = {}
    if status == 'closed':
        tally_rows = conn.execute(
            "SELECT choice, COUNT(*) as cnt FROM votes WHERE role=? GROUP BY choice",
            (role,)
        ).fetchall()
        tally = {r['choice']: r['cnt'] for r in tally_rows}

    conn.close()

    return jsonify({
        "role":      role,
        "status":    status,
        "choices":   [r['choice'] for r in rows],
        "has_voted": existing is not None,
        "tally":     tally,
    })
