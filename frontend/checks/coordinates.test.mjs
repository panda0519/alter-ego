import { test } from 'node:test';
import assert from 'node:assert/strict';
import { validCoordinates } from '../src/data/coordinates.ts';

test('valid ordinary, boundary, zero and duplicate coordinates remain usable', () => {
  for (const pair of [[26, 91], [0, 0], [-90, -180], [90, 180], [26, 91]]) {
    assert.equal(validCoordinates(...pair), true);
  }
});
test('invalid, missing, nonfinite, string and out-of-range coordinates are rejected', () => {
  for (const pair of [[null, 91], [26, undefined], [NaN, 91], [26, Infinity], [-Infinity, 0], ['26', 91], [0, '91'], [90.001, 0], [-90.001, 0], [0, 180.001], [0, -180.001]]) {
    assert.equal(validCoordinates(...pair), false);
  }
});
