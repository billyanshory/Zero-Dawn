import re

with open("sekolah-luar-biasa-65 ( idcloudhost - Migration Database & Code Interaction - PostgreSQL + stay with SQLAchemy ORM - Second Effort ).py", "r") as f:
    content = f.read()

# Fix the bare excepts
content = re.sub(
r"""        return settings
    except:
        settings = \{\}""",
"""        return settings
    except Exception:
        app.logger.warning("Failed to load app settings", exc_info=True)
        settings = {}""", content)

content = re.sub(
r"""        db\.session\.close\(\)
    except:
        epilepsi_logs = \[\]""",
"""        db.session.close()
    except Exception:
        app.logger.warning("Failed to load epilepsi logs", exc_info=True)
        epilepsi_logs = []""", content)

content = re.sub(
r"""        except:
            pass # Skip invalid dates""",
"""        except (ValueError, TypeError):
            pass # Skip invalid dates""", content)

content = re.sub(
r"""            except:
                medications = \[\]""",
"""            except (json.JSONDecodeError, TypeError):
                medications = []""", content)


# Fix the rollback in therapy_log
content = content.replace(
"""        db.session.commit()
    except Exception as e:
        app.logger.error(f"Error logging therapy: {e}", exc_info=True)
    return redirect(url_for('index', open='modal-terapi-log'))""",
"""        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error('Database commit error', exc_info=True)
    except Exception as e:
        app.logger.error(f"Error logging therapy: {e}", exc_info=True)
    return redirect(url_for('index', open='modal-terapi-log'))"""
)

with open("sekolah-luar-biasa-65 ( idcloudhost - Migration Database & Code Interaction - PostgreSQL + stay with SQLAchemy ORM - Second Effort ).py", "w") as f:
    f.write(content)
