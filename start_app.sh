#!/bin/bash
python "kampus-stie-samarinda-12 ( idcloudhost - sistematika mekanisme - ekosistem keseluruhan website stiesam ).py" > flask_app.log 2>&1 &
echo $! > flask_app.pid
