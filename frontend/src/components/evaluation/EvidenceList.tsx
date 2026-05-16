import type { EvidenceItem } from '@/lib/types';

interface StringListProps {
  items: string[];
  title: string;
  type?: 'evidence' | 'strength' | 'weakness';
}

interface EvidenceItemListProps {
  items: EvidenceItem[];
  title: string;
}

type Props = StringListProps | EvidenceItemListProps;

function isEvidenceItemList(props: Props): props is EvidenceItemListProps {
  return (
    'items' in props &&
    Array.isArray(props.items) &&
    props.items.length > 0 &&
    typeof (props.items as EvidenceItem[])[0] === 'object' &&
    'finding' in (props.items as EvidenceItem[])[0]
  );
}

const impactColors: Record<EvidenceItem['impact'], string> = {
  high: 'bg-red-900/30 text-red-400 border-red-800/40',
  medium: 'bg-yellow-900/30 text-yellow-400 border-yellow-800/40',
  low: 'bg-[#252630] text-[#9a9ba8] border-[#3a3b48]',
};

const typeAccent: Record<string, string> = {
  evidence: 'text-brand-400',
  strength: 'text-emerald-400',
  weakness: 'text-red-400',
};

const typeBullet: Record<string, string> = {
  evidence: '›',
  strength: '+',
  weakness: '−',
};

export function EvidenceList(props: Props) {
  const { items, title } = props;
  if (!items || items.length === 0) return null;

  if (isEvidenceItemList(props)) {
    return (
      <div>
        <h4 className="text-xs font-semibold text-[#7e8088] uppercase tracking-wider mb-2">
          {title}
        </h4>
        <ul className="space-y-2">
          {(items as EvidenceItem[]).map((item, i) => (
            <li
              key={i}
              className="bg-[#1c1d25] border border-[#2d2e3a] rounded-lg px-3 py-2.5"
            >
              <div className="flex items-start gap-2">
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-[#dddfe4] leading-snug">{item.finding}</p>
                  {item.file_ref && (
                    <p className="text-xs text-brand-400 font-mono mt-1 truncate">
                      {item.file_ref}
                    </p>
                  )}
                </div>
                <span
                  className={`flex-shrink-0 text-xs px-2 py-0.5 rounded border font-semibold uppercase tracking-wide ${
                    impactColors[item.impact] ?? impactColors.low
                  }`}
                >
                  {item.impact}
                </span>
              </div>
            </li>
          ))}
        </ul>
      </div>
    );
  }

  const { type = 'evidence' } = props as StringListProps;
  const accent = typeAccent[type] ?? 'text-[#9a9ba8]';
  const bullet = typeBullet[type] ?? '›';

  return (
    <div>
      <h4 className="text-xs font-semibold text-[#7e8088] uppercase tracking-wider mb-2">
        {title}
      </h4>
      <ul className="space-y-1.5">
        {(items as string[]).map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-[#9a9ba8]">
            <span className={`${accent} mt-0.5 flex-shrink-0 font-bold`}>{bullet}</span>
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
