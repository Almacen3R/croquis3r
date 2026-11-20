import test from 'node:test';
import assert from 'node:assert/strict';
import {recalculateWithSettings} from '../src/static/croquis/calculation-flow.mjs';
test('recalculate applies the selected 2.7 m height before requesting materials',async()=>{
 let height=2.5;const calls=[];
 await recalculateWithSettings(true,async()=>{await Promise.resolve();height=2.7;calls.push('applied');return true;},()=>{calls.push('calculated');assert.equal(height,2.7);});
 assert.deepEqual(calls,['applied','calculated']);
});
test('invalid or rejected settings do not recalculate the previous height',async()=>{
 let requests=0;
 await recalculateWithSettings(true,async()=>false,()=>requests++);
 assert.equal(requests,0);
 await assert.rejects(recalculateWithSettings(true,async()=>{throw new Error('Invalid settings');},()=>requests++),/Invalid settings/);
 assert.equal(requests,0);
});
test('unchanged configuration recalculates directly',async()=>{
 let requests=0;
 await recalculateWithSettings(false,()=>{throw new Error('Should not apply');},()=>requests++);
 assert.equal(requests,1);
});
