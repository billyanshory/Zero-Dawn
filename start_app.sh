#!/bin/bash
export FLASK_APP="sekolah-luar-biasa-79 ( idcloudhost - Sixteenth Layer of Quality Control - Frontend Quality & UX - v.78 - Opus 4.6 Ex. Think ).py"
export FLASK_ENV=development
export SECRET_KEY="test_secret_key"
export SQLALCHEMY_DATABASE_URI="sqlite:///slb.db"
export FLASK_INIT_DB=1

python "$FLASK_APP" > flask_output.log 2>&1 &
echo $! > flask_pid.txt
