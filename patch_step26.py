with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "r") as f:
    text = f.read()

search1 = """        device_id = f"{device_name} [{request.sid[:4]}]"
        _connected_clients.add(request.sid, device_id)
        emit('client_count', {'count': _connected_clients.count(), 'clients': list(_connected_clients.snapshot().values())}, broadcast=True)
    except Exception:"""

replace1 = """        device_id = f"{device_name} [{request.sid[:4]}]"
        _connected_clients.add(request.sid, device_id)
        emit('client_count', {'count': _connected_clients.count()}, broadcast=True)
    except Exception:"""

search2 = """        if not session.get('user_id'):
            return
        _connected_clients.remove(request.sid)
        emit('client_count', {'count': _connected_clients.count(), 'clients': list(_connected_clients.snapshot().values())}, broadcast=True)
    except Exception:"""

replace2 = """        if not session.get('user_id'):
            return
        _connected_clients.remove(request.sid)
        emit('client_count', {'count': _connected_clients.count()}, broadcast=True)
    except Exception:"""

if search1 in text and search2 in text:
    text = text.replace(search1, replace1)
    text = text.replace(search2, replace2)
    with open("sekolah-luar-biasa-90 ( idcloudhost - Nineteenth Layer of Quality Control - Data Privacy & Compliance (SLB-Specific) - v.89 - Opus 4.7 Ad. Think ).py", "w") as f:
        f.write(text)
    print("Success")
else:
    print("Search string not found")
