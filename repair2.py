import re

with open("sekolah_luar_biasa.py", "r") as f:
    content = f.read()

# 4. Bare Excepts (Findings 11) - Missed due to slightly different initial replacement structure
content = content.replace(
"""        return settings
    except:
        settings = {}""",
"""        return settings
    except Exception:
        app.logger.warning("Failed to load app settings", exc_info=True)
        settings = {}"""
)

content = content.replace(
"""        db.session.close()
    except:
        epilepsi_logs = []""",
"""        db.session.close()
    except Exception:
        app.logger.warning("Failed to load epilepsi logs", exc_info=True)
        epilepsi_logs = []"""
)

content = content.replace(
"""        except:
            pass # Skip invalid dates""",
"""        except (ValueError, TypeError):
            pass # Skip invalid dates"""
)

content = content.replace(
"""            except:
                medications = []""",
"""            except (json.JSONDecodeError, TypeError):
                medications = []"""
)

# 8. Print (Finding 10) - Missing therapy_log print
content = content.replace(
"""        print(f"Error logging therapy: {e}")""",
"""        app.logger.error(f"Error logging therapy: {e}", exc_info=True)"""
)


with open("sekolah_luar_biasa.py", "w") as f:
    f.write(content)
