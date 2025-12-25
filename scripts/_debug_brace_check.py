from pathlib import Path
p=Path('qaco_client_onboarding/static/src/scss/onboarding.scss')
s=p.read_text(encoding='utf-8')
open_count=0
for i,line in enumerate(s.splitlines(),1):
    open_count+=line.count('{')
    open_count-=line.count('}')
    if open_count<0:
        print('Too many } at line',i)
        break
print('Final balance',open_count)
# print surrounding lines for last few lines
lines=s.splitlines()
for i in range(max(1,i-6), min(len(lines), i+6)+1):
    print(i, lines[i-1])
