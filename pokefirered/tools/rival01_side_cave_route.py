import subprocess,sys,json
from pathlib import Path
steps=[('MtMoon_B2F',31,11,'back-side-stair'),('MtMoon_B1F',25,4,'side-cave-exit'),('MtMoon_1F',5,6,'main-entrance-stair'),('MtMoon_B1F',22,18,'fossil-main-entrance')]
for m,x,y,label in steps:
 command=['.venv/bin/python','tools/rival01_travel.py',m,str(x),str(y),'--label',label]
 with open('evidence/phase8/rival01/'+label+'-console.log','w') as f:
  r=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
 if r.returncode:sys.exit(r.returncode)
 history=json.load(open('evidence/phase8/rival01/'+label+'-travel.json'))
 if history[-1]['status']!='map-transition':print(history[-1],flush=True);sys.exit(2)
 print(label+': '+history[-1]['map'],flush=True)
