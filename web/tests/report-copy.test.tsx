import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import App from '../src/App';

const report = {
  source: '试验重复5次。', output: '试验重复5次。', status: 'unchanged',
  warnings: ['human_review_required', 'original_retained_in_some_segments', 'unknown_report_warning'],
  model: 'local-test', elapsed_seconds: 0.2, requires_review: true, detector_status: 'not_run',
  source_sha256: 'source-hash', output_sha256: 'output-hash',
  segments: [{
    id: 0, original: '试验重复5次。', output: '试验重复5次。', status: 'retained',
    audit: { blocked: true, requires_review: true, issues: [
      { code: 'numbers', severity: 'error', before: '{"5次":1}', after: '{"6次":1}' },
      { code: 'negation', severity: 'warning', before: '{}', after: '{"不":1}' },
      { code: 'unknown_check', severity: 'unknown_severity', before: 'original', after: 'changed' },
    ] },
    attempts: [{ text: '', audit: null, error: 'model_output_truncated' }],
  }],
};

async function showReport() {
  vi.stubGlobal('fetch', async (url: string) => new Response(JSON.stringify(url === '/api/health'
    ? { model_ready: true, model: 'local-test', detector_configured: false, version: '0.1.0', default_language: 'zh' }
    : report), { headers: { 'Content-Type': 'application/json' } }));
  render(<App />);
  fireEvent.change(screen.getByLabelText('原文'), { target: { value: report.source } });
  await userEvent.click(screen.getByRole('button', { name: '开始改写' }));
  await waitFor(() => expect(screen.getByLabelText('改写稿')).toHaveValue(report.output));
}

it('explains known audit codes in Chinese and identifies rejected candidate checks', async () => {
  await showReport();
  expect(screen.getByText('数字或单位发生变化')).toBeInTheDocument();
  expect(screen.getByText('否定表达发生变化')).toBeInTheDocument();
  expect(screen.getByText('错误')).toBeInTheDocument();
  expect(screen.getByText('警告')).toBeInTheDocument();
  expect(screen.getByText('请人工核对论点、数据和引用。')).toBeInTheDocument();
  expect(screen.getByText('部分段落未采用候选稿，已保留原文。')).toBeInTheDocument();
  expect(screen.getByText('未采用候选的检查结果')).toBeInTheDocument();
  expect(screen.queryByText('存在内容风险')).not.toBeInTheDocument();
  await userEvent.click(screen.getByText('候选记录'));
  expect(screen.getByText('模型输出被截断，未采用该候选。')).toBeInTheDocument();
  for (const code of ['numbers', 'negation', 'error', 'warning', 'human_review_required', 'original_retained_in_some_segments', 'model_output_truncated']) expect(screen.queryByText(code, { exact: true })).not.toBeInTheDocument();
  expect(screen.getByText('unknown_check')).toBeInTheDocument();
  expect(screen.getByText('unknown_severity')).toBeInTheDocument();
  expect(screen.getByText('unknown_report_warning')).toBeInTheDocument();
});

it('switches the same check explanations to English without changing the draft', async () => {
  await showReport();
  await userEvent.click(screen.getByRole('button', { name: 'English' }));
  expect(screen.getByText('Numbers or units changed')).toBeInTheDocument();
  expect(screen.getByText('Negation changed')).toBeInTheDocument();
  expect(screen.getByText('Error')).toBeInTheDocument();
  expect(screen.getByText('Warning')).toBeInTheDocument();
  expect(screen.getByText('Review arguments, data and citations manually.')).toBeInTheDocument();
  expect(screen.getByText('Some candidates were not used; the source was retained.')).toBeInTheDocument();
  expect(screen.getByText('Checks for an unused candidate')).toBeInTheDocument();
  await userEvent.click(screen.getByText('Candidate history'));
  expect(screen.getByText('Model output was truncated; this candidate was not used.')).toBeInTheDocument();
  expect(screen.getByLabelText('Rewrite')).toHaveValue('试验重复5次。');
});

it('preserves machine codes in JSON exports despite translated inspection labels', async () => {
  const blobs: Blob[] = [];
  vi.stubGlobal('URL', Object.assign(URL, { createObjectURL: (blob: Blob) => { blobs.push(blob); return 'blob:report'; }, revokeObjectURL: () => {} }));
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
  await showReport();
  expect(screen.getByText('数字或单位发生变化')).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: '导出 JSON' }));
  const raw = await new Promise<string>(resolve => { const reader = new FileReader(); reader.onload = () => resolve(String(reader.result)); reader.readAsText(blobs[0]); });
  const exported = JSON.parse(raw);
  expect(exported.warnings).toEqual(['human_review_required', 'original_retained_in_some_segments', 'unknown_report_warning']);
  expect(exported.segments[0].audit.issues[0]).toEqual({ code: 'numbers', severity: 'error', before: '{"5次":1}', after: '{"6次":1}' });
  expect(exported.segments[0].attempts[0].error).toBe('model_output_truncated');
});

it('labels warning-only retained candidates as unused rather than source damage', async () => {
  const warningOnly = { ...report, segments: [{ ...report.segments[0], audit: { blocked: false, requires_review: true, issues: [{ code: 'negation', severity: 'warning', before: '{}', after: '{"不":1}' }] } }] };
  vi.stubGlobal('fetch', async (url: string) => new Response(JSON.stringify(url === '/api/health'
    ? { model_ready: true, model: 'local-test', detector_configured: false, version: '0.1.0', default_language: 'zh' }
    : warningOnly)));
  render(<App />);
  fireEvent.change(screen.getByLabelText('原文'), { target: { value: report.source } });
  await userEvent.click(screen.getByRole('button', { name: '开始改写' }));
  expect(await screen.findByText('未采用候选的检查结果')).toBeInTheDocument();
  expect(screen.queryByText('存在内容风险')).not.toBeInTheDocument();
});

it('explains candidates requiring manual review in both interface languages', async () => {
  const manualWarning = { ...report, warnings: ['candidates_require_manual_review'] };
  vi.stubGlobal('fetch', async (url: string) => new Response(JSON.stringify(url === '/api/health'
    ? { model_ready: true, model: 'local-test', detector_configured: false, version: '0.1.0', default_language: 'zh' }
    : manualWarning)));
  render(<App />);
  fireEvent.change(screen.getByLabelText('原文'), { target: { value: report.source } });
  await userEvent.click(screen.getByRole('button', { name: '开始改写' }));
  expect(await screen.findByText('部分候选存在措辞或声明变化，已保留供人工核对。')).toBeInTheDocument();
  expect(screen.queryByText('candidates_require_manual_review')).not.toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: 'English' }));
  expect(screen.getByText('Some candidates change wording or disclosures and have been kept for manual review.')).toBeInTheDocument();
  expect(screen.queryByText('candidates_require_manual_review')).not.toBeInTheDocument();
});

it('explains permission, obligation and provenance warnings in both languages', async () => {
  const cues = { ...report, segments: [{ ...report.segments[0], audit: {
    blocked: false, requires_review: true, issues: ['permission', 'obligation', 'provenance', 'purpose'].map(code => ({ code, severity: 'warning', before: '{}', after: '{}' })),
  } }] };
  vi.stubGlobal('fetch', async (url: string) => new Response(JSON.stringify(url === '/api/health'
    ? { model_ready: true, model: 'local-test', detector_configured: false, version: '0.1.0', default_language: 'zh' }
    : cues)));
  render(<App />);
  fireEvent.change(screen.getByLabelText('原文'), { target: { value: report.source } });
  await userEvent.click(screen.getByRole('button', { name: '开始改写' }));
  expect(await screen.findByText('许可或能力措辞发生变化')).toBeInTheDocument();
  expect(screen.getByText('要求性措辞发生变化')).toBeInTheDocument();
  expect(screen.getByText('来源或虚构声明发生变化')).toBeInTheDocument();
  expect(screen.getByText('用途表达发生变化')).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: 'English' }));
  for (const label of ['Permission or ability wording changed', 'Requirement wording changed', 'Provenance or fictional-data disclosure changed', 'Purpose wording changed']) expect(screen.getByText(label)).toBeInTheDocument();
  expect(screen.getByLabelText('Rewrite')).toHaveValue(report.output);
});

it('explains rejected reasoning output in Chinese and English', async () => {
  const reasoningReport = { ...report, status: 'failed', segments: [{ ...report.segments[0], status: 'failed', attempts: [{ text: '', audit: null, error: 'model_reasoning_output' }] }] };
  vi.stubGlobal('fetch', async (url: string) => new Response(JSON.stringify(url === '/api/health'
    ? { model_ready: true, model: 'local-test', detector_configured: false, version: '0.1.0', default_language: 'zh' }
    : reasoningReport)));
  render(<App />);
  fireEvent.change(screen.getByLabelText('原文'), { target: { value: report.source } });
  await userEvent.click(screen.getByRole('button', { name: '开始改写' }));
  await userEvent.click(await screen.findByText('候选记录'));
  expect(screen.getByText('模型返回了思考内容，未作为改写稿采用。')).toBeInTheDocument();
  expect(screen.queryByText('model_reasoning_output')).not.toBeInTheDocument();
  await userEvent.click(screen.getByRole('button', { name: 'English' }));
  expect(screen.getByText('The model returned reasoning content; it was not used as a rewrite.')).toBeInTheDocument();
  expect(screen.queryByText('model_reasoning_output')).not.toBeInTheDocument();
});
