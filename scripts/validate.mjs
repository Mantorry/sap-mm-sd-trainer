import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const questions=JSON.parse(readFileSync('data/questions.json','utf8'));
assert.equal(questions.length,500,'В банке должно быть 500 вопросов');
assert.equal(questions.filter(q=>q.module==='MM').length,250,'Нужно 250 вопросов MM');
assert.equal(questions.filter(q=>q.module==='SD').length,250,'Нужно 250 вопросов SD');
assert.equal(new Set(questions.map(q=>q.id)).size,500,'ID уникальны');
assert.equal(new Set(questions.map(q=>q.question)).size,500,'Тексты уникальны');
assert.ok(questions.some(q=>q.type==='multi'));
assert.ok(questions.some(q=>q.type==='tf'));
assert.ok(questions.some(q=>/Ситуацион|MIRO|MIGO|по цене|разница|отпуск/.test(q.question)));
for(const q of questions){
 assert.ok(q.question.length>30 && q.explanation.length>12,`Вопрос ${q.id} — не заполнен`);
 assert.ok(['single','multi','tf'].includes(q.type),`Вопрос ${q.id} — тип`);
 assert.equal(q.options.length,q.type==='tf'?2:4,`Вопрос ${q.id} — варианты`);
 const ids=q.options.map(o=>o.id);assert.equal(new Set(ids).size,ids.length,`Вопрос ${q.id} — ID вариантов`);
 const right=q.options.filter(o=>o.correct).length;
 assert.ok(q.type==='multi'?(right>=2&&right<=3):right===1,`Вопрос ${q.id} — правильные варианты`);
 assert.ok(q.options.every(o=>o.label.length>=1 && o.feedback.length>=12),`Вопрос ${q.id} — обоснования`);
}
for(const file of ['assets/app.js','config.js'])new vm.Script(readFileSync(file,'utf8'),{filename:file});
for(const file of ['index.html','leaderboard.html']){
 const html=readFileSync(file,'utf8');assert.ok(html.includes('assets/app.js')&&html.includes('config.js'));
}
// Simulate independent seeded permutations without repeating question IDs.
function rng(seed){let s=seed>>>0;return()=>{s+=0x6D2B79F5;let t=s;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296}}
function shuffle(arr,seed){const out=arr.slice(),rand=rng(seed);for(let i=out.length-1;i>0;i--){const j=Math.floor(rand()*(i+1));[out[i],out[j]]=[out[j],out[i]]}return out}
for(const seed of [123456,987654,1,2,3,4294967295]){
 const mm=shuffle(questions.filter(q=>q.module==='MM'),seed^0x98ad3127),sd=shuffle(questions.filter(q=>q.module==='SD'),seed^0x83b51c7d);
 const ids=[];for(let i=0;i<25;i++){const set=[...mm.slice(i*10,i*10+10),...sd.slice(i*10,i*10+10)];assert.equal(set.length,20);assert.equal(set.filter(q=>q.module==='MM').length,10);assert.equal(set.filter(q=>q.module==='SD').length,10);ids.push(...set.map(q=>q.id))}
 assert.equal(new Set(ids).size,500,'Вопросы должны не повторяться');
}
console.log('PASS: 500 уникальных вопросов; MM 250 / SD 250; 25 × 20 с 10 MM и 10 SD; синтаксис и файлы в порядке.');
