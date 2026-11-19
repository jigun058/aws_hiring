const SIZE = {
  lg: 'h-[54px] px-7 text-[18px]', md: 'h-[44px] px-5 text-[16px]', sm: 'h-[40px] px-3.5 text-[15px]', xl: 'h-[56px] px-8 text-[19px]',
}
const KIND = {
  primary: 'border-0 bg-brand text-white hover:bg-brand-dark',
  outline: 'border-[1.5px] border-brand bg-white text-brand hover:bg-hover',
  plain: 'border border-field bg-white text-body hover:border-brand',
}
export function Btn({ kind = 'primary', size = 'md', className = '', ...p }) {
  return <button {...p} className={`rounded-full font-bold whitespace-nowrap disabled:opacity-50 ${SIZE[size]} ${KIND[kind]} ${className}`} />
}

// 선택형 알약 버튼(필터·경험 종류)
export function Pill({ on, className = '', children, ...p }) {
  return (
    <button aria-pressed={on} {...p}
      className={`h-[48px] px-[18px] rounded-full bg-white text-[16px] ${on ? 'border-2 border-brand text-brand font-extrabold' : 'border border-field text-body hover:border-brand'} ${className}`}>
      {children}
    </button>
  )
}

export const Spinner = ({ size = 48, w = 4 }) => <div className="spin shrink-0" style={{ width: size, height: size, borderWidth: w }} />
export const AiDot = ({ size = 10 }) => <span className="ai-dot" style={{ width: size, height: size }} />

export function Logo({ small }) {
  return (
    <div className="flex items-center gap-2.5">
      <div className="relative shrink-0 rounded-full border-[3.5px] border-brand" style={{ width: small ? 32 : 34, height: small ? 32 : 34 }}>
        <div className="absolute size-[10px] rounded-full bg-[#3FA9E6]" style={{ right: small ? 2 : 3, top: small ? 2 : 3 }} />
      </div>
      <div className="flex flex-col leading-[1.1] text-left">
        <span className={`font-extrabold text-ink ${small ? 'text-[20px]' : 'text-[21px]'}`}>CareerLens</span>
        <span className={`font-bold text-sub ${small ? 'text-[12px]' : 'text-[13px]'}`}>커리어렌즈</span>
      </div>
    </div>
  )
}

// P3 근거 등급
export const GRADE = { L3: ['성과 확인', 'text-ok', '결과가 숫자나 사실로 확인돼요'], L2: ['수행 확인', 'text-brand', '해 본 일이 확인돼요'], L1: ['학습만', 'text-sub', '배웠지만 일로 해 본 기록은 없어요'] }
export const Grade = ({ lv }) => GRADE[lv] ? <span className={`shrink-0 text-[14px] font-bold ${GRADE[lv][1]}`}>{GRADE[lv][0]}</span> : null

export function H1({ title, sub }) {
  return (
    <div>
      <h1 className="m-0 mb-2.5 text-[34px] font-extrabold text-ink leading-[1.35] tracking-[-0.02em]">{title}</h1>
      {sub && <p className="m-0 text-[18px] text-sub">{sub}</p>}
    </div>
  )
}

export function EmptyArt({ size = 88 }) {
  return (
    <div className="rounded-full border-[1.5px] border-field flex items-center justify-center" style={{ width: size, height: size }}>
      <div className="w-[34px] h-[42px] rounded-md border-[2.5px] border-dashed border-dash" />
    </div>
  )
}

export const won = n => n === 0 ? '무료' : n ? `${n.toLocaleString('ko-KR')}원` : '공고에 없음'
