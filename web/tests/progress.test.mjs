import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeProgress,restoreProgress,mergeProgress} from '../src/progress.mjs';
const id='docs/android-interview-handbook.md#n01';
function record(mastery='review',updatedAt='2026-11-01T10:00:00Z'){return {mastery,favorite:true,updatedAt};}
test('absent data starts empty; malformed or unsupported data retains exact recovery backup',()=>{
  assert.equal(Object.keys(restoreProgress(null).progress.items).length,0);
  for(const raw of ['{broken','null','[]',JSON.stringify({version:9,items:{[id]:record()}})]){
    const result=restoreProgress(raw);
    assert.equal(result.recoveryRaw,raw);assert.ok(result.warning);assert.equal(Object.keys(result.progress.items).length,0);
  }
});
test('legacy unversioned and v0 maps migrate to v1 without changing stable IDs',()=>{
  for(const version of [undefined,0]){
    const parsed=normalizeProgress({version,progress:{[id]:record()}});
    assert.equal(parsed.version,1);assert.equal(parsed.items[id].mastery,'review');assert.equal(parsed.items[id].favorite,true);
  }
});
test('invalid fields and prototype-like IDs cannot become executable properties',()=>{
  const data=JSON.parse('{"version":1,"items":{"__proto__":{"mastery":"mastered"},"constructor":{},"safe":{"mastery":"unknown","favorite":"yes","updatedAt":"invalid","seenAt":42},"array":[]}}');
  const parsed=normalizeProgress(data);
  assert.equal(Object.getPrototypeOf(parsed.items),null);
  assert.equal(parsed.items.__proto__,undefined);assert.equal(parsed.items.constructor,undefined);assert.equal(parsed.items.array,undefined);
  assert.deepEqual(parsed.items.safe,{mastery:'new',favorite:false,updatedAt:null,seenAt:null});
});
test('import preserves newer current progress and merges newer incoming and orphan records',()=>{
  const current={version:1,items:{[id]:record('mastered','2026-11-01T12:00:00Z'),'removed-question':record()}};
  const old=mergeProgress(current,{version:1,items:{[id]:record('new','2026-10-01T12:00:00Z'),'new-question':record()}});
  assert.equal(old.progress.items[id].mastery,'mastered');assert.equal(old.count,1);
  assert.ok(old.progress.items['removed-question']);assert.ok(old.progress.items['new-question']);
  const newer=mergeProgress(current,{version:1,items:{[id]:record('review','2026-11-01T13:00:00Z')}});
  assert.equal(newer.progress.items[id].mastery,'review');assert.equal(newer.count,1);
  assert.equal(current.items[id].mastery,'mastered');
});
test('import bounds prohibit oversized mappings and invalid top-level structures',()=>{
  assert.throws(()=>normalizeProgress({version:1,items:[]}),/有效/);
  const items=Object.fromEntries(Array.from({length:10001},(_,i)=>['id'+i,record()]));
  assert.throws(()=>normalizeProgress({version:1,items}),/数量/);
});
