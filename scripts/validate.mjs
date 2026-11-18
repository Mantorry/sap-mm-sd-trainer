import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const html = readFileSync('index.html','utf8');
assert.match(html, /<html lang="ru">/);
assert.match(html, /<\/html>/);
const script = html.match(/<script>([\s\S]*?)<\/script>/)?.[1];
assert.ok(script,'Отсутствует встроенный скрипт');
new vm.Script(script,{filename:'trainer.js'});
const json = script.match(/const BANK = (\[[\s\S]*?\]);\s*const /)?.[1];
assert.ok(json,'Не найден банк вопросов');
const bank = JSON.parse(json);
assert.equal(bank.length,500,'Должно быть 500 вопросов');
const ids=new Set(bank.map(q=>q.id));
assert.equal(ids.size,500,'ID должны быть уникальными');
for(const q of bank){
 assert.ok(q.question && q.explanation,'Вопрос и пояснение обязательны');
 assert.ok(['single','multi','tf'].includes(q.type),'Некорректный тип');
 assert.ok(Array.isArray(q.options) && q.options.length>=2,'Отсутствуют варианты');
 assert.ok(q.options.some(o=>o.correct),'Нет правильного ответа');
 assert.ok(q.options.every(o=>typeof o.feedback==='string' && o.feedback.length>3),'Отсутствует объяснение варианта');
}
console.log('Успешная проверка: 500 вопросов, корректный JavaScript и пояснения.');
