import type { Language } from './types';

type Category = 'issues' | 'severity' | 'warnings' | 'errors' | 'context';
const labels: Record<Language, Record<Category, Record<string, string>>> = {
  zh: {
    issues: {
      invalid_output: '候选稿内容或格式无效',
      numbers: '数字或单位发生变化',
      comparisons: '比较符号或关系发生变化',
      citations: '引用标记发生变化',
      urls: '网址发生变化',
      latex: '公式发生变化',
      code: '代码发生变化',
      protected_terms: '指定保留的术语发生变化',
      negation: '否定表达发生变化',
      certainty: '确定性措辞发生变化',
      permission: '许可或能力措辞发生变化',
      obligation: '要求性措辞发生变化',
      provenance: '来源或虚构声明发生变化',
      purpose: '用途表达发生变化',
    },
    severity: { error: '错误', warning: '警告' },
    warnings: {
      human_review_required: '请人工核对论点、数据和引用。',
      original_retained_in_some_segments: '部分段落未采用候选稿，已保留原文。',
      candidates_require_manual_review: '部分候选存在措辞或声明变化，已保留供人工核对。',
    },
    errors: {
      model_response_too_large: '模型响应超出大小限制。',
      model_unavailable_or_invalid_response: '模型不可用或响应无效。',
      model_invalid_response: '模型响应格式无效。',
      model_output_truncated: '模型输出被截断，未采用该候选。',
      model_empty_or_invalid_output: '模型输出为空或无效，未采用该候选。',
      model_reasoning_output: '模型返回了思考内容，未作为改写稿采用。',
    },
    context: { rejected_candidate: '未采用候选的检查结果' },
  },
  en: {
    issues: {
      invalid_output: 'Candidate content or format is invalid',
      numbers: 'Numbers or units changed',
      comparisons: 'Comparison signs or relations changed',
      citations: 'Citation markers changed',
      urls: 'URLs changed',
      latex: 'Equations changed',
      code: 'Code changed',
      protected_terms: 'Protected terms changed',
      negation: 'Negation changed',
      certainty: 'Certainty wording changed',
      permission: 'Permission or ability wording changed',
      obligation: 'Requirement wording changed',
      provenance: 'Provenance or fictional-data disclosure changed',
      purpose: 'Purpose wording changed',
    },
    severity: { error: 'Error', warning: 'Warning' },
    warnings: {
      human_review_required: 'Review arguments, data and citations manually.',
      original_retained_in_some_segments: 'Some candidates were not used; the source was retained.',
      candidates_require_manual_review: 'Some candidates change wording or disclosures and have been kept for manual review.',
    },
    errors: {
      model_response_too_large: 'Model response exceeded the size limit.',
      model_unavailable_or_invalid_response: 'The model is unavailable or its response is invalid.',
      model_invalid_response: 'Model response format is invalid.',
      model_output_truncated: 'Model output was truncated; this candidate was not used.',
      model_empty_or_invalid_output: 'Model output was empty or invalid; this candidate was not used.',
      model_reasoning_output: 'The model returned reasoning content; it was not used as a rewrite.',
    },
    context: { rejected_candidate: 'Checks for an unused candidate' },
  },
};

export function reportCopy(locale: Language, category: Category, code: string): string {
  const categoryLabels = labels[locale][category];
  return Object.hasOwn(categoryLabels, code) ? categoryLabels[code] : code;
}
