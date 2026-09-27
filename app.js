'use strict';
let dataset;
const $ = id => document.getElementById(id);
const rm = value => 'RM' + Math.round(value).toLocaleString('en-MY');
const signed = value => (value >= 0 ? '+' : '') + value.toFixed(1) + '%';
function percentileBand(income, bands) {
  // Adjacent sampled bands may touch or have small gaps due to survey rounding.
  // Prefer a containing band; otherwise the nearest median is an estimate.
  let found = bands.find(b => b.minimum !== null && b.maximum !== null && income >= b.minimum && income <= b.maximum);
  if (!found) {
    found = bands.reduce((a, b) => Math.abs(b.median - income) < Math.abs(a.median - income) ? b : a);
  }
  return found;
}
function render(income) {
  const {medians, selangor_percentiles: bands, category_thresholds: limits, survey_year: year} = dataset;
  const group = income < limits.m40 ? 'B40' : income < limits.t20 ? 'M40' : 'T20';
  $('category').textContent = group;
  $('categoryCaption').textContent = 'National · ' + year + ' thresholds';
  for (const [name, value, delta] of [['Malaysia','myMedian','myDelta'],['Selangor','selMedian','selDelta'],['Kuala Langat','klMedian','klDelta']]) {
    $(value).textContent = rm(medians[name]);
    $(delta).textContent = signed((income / medians[name] - 1) * 100) + ' vs median';
  }
  const band = percentileBand(income, bands);
  $('summary').textContent = `At ${rm(income)} gross per month, your household is classified ${group} nationally. You are ${rm(Math.abs(income - medians['Kuala Langat']))} ${income >= medians['Kuala Langat'] ? 'above' : 'below'} the Kuala Langat median and ${rm(Math.abs(income - medians.Selangor))} ${income >= medians.Selangor ? 'above' : 'below'} the Selangor median.`;
  $('percentile').textContent = `Selangor survey estimate: around percentile group P${band.percentile} (group median ${rm(band.median)}). Each group covers about 1% of surveyed households; this is an approximate band, not your exact rank.`;
  const scale = Math.max(15000, Math.ceil(Math.max(income, ...Object.values(medians)) / 5000) * 5000);
  $('bars').replaceChildren(...Object.entries(medians).map(([name, median]) => {
    const row = document.createElement('div'); row.className = 'barrow';
    const title = document.createElement('b'); title.textContent = name;
    const track = document.createElement('div'); track.className = 'track';
    const fill = document.createElement('div'); fill.className = 'fill'; fill.style.width = median / scale * 100 + '%';
    const marker = document.createElement('div'); marker.className = 'marker'; marker.style.left = Math.min(99, income / scale * 100) + '%';
    track.append(fill, marker);
    const label = document.createElement('b'); label.textContent = rm(median);
    row.append(title, track, label); return row;
  }));
  $('analysis').classList.remove('hidden');
  $('prompt').textContent = 'Analysis uses ' + year + ' DOSM survey data. Enter another amount to compare.';
}
fetch('data/income.json', {cache:'no-cache'}).then(r => {if(!r.ok) throw new Error('Data unavailable'); return r.json()}).then(data => {
  if (!data.medians || data.selangor_percentiles?.length !== 100) throw new Error('Invalid data');
  dataset = data;
  $('year').textContent = data.survey_year;
  for (const [name,id] of [['Malaysia','myMedian'],['Selangor','selMedian'],['Kuala Langat','klMedian']]) $(id).textContent = rm(data.medians[name]);
}).catch(() => { $('prompt').textContent = 'DOSM data could not load. Please refresh the page.'; $('prompt').classList.add('error'); });
$('form').addEventListener('submit', event => {
  event.preventDefault();
  if (!dataset) return;
  const raw = $('income').value.trim(), income = Number(raw);
  if (raw === '' || !Number.isFinite(income) || income < 0) { $('prompt').textContent = 'Enter a valid non-negative amount.'; $('prompt').classList.add('error'); return; }
  $('prompt').classList.remove('error'); render(income);
});
