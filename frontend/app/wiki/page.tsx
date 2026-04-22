'use client';

import { useState } from 'react';
import { useLang } from '@/components/layout/LangProvider';
import { NeoCard } from '@/components/ui/NeoCard';
import { NeoButton } from '@/components/ui/NeoButton';
import { t } from '@/lib/i18n';
import { Search, BookOpen } from 'lucide-react';

export default function WikiPage() {
  const { lang } = useLang();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    // In real implementation, fetch from backend RAG API
    setTimeout(() => {
      setResults([
        { title: 'Drawdown', score: 0.85, content: 'Drawdown is the peak-to-trough decline...' },
        { title: 'Trend Following', score: 0.72, content: 'Trend following is a trading strategy...' },
      ]);
      setLoading(false);
    }, 500);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-black uppercase tracking-wider">{t('tradingWiki', lang)}</h2>

      <NeoCard>
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder={t('searchPlaceholder', lang)}
            className="flex-1 border-[3px] border-neo-stroke px-4 py-3 bg-neo-surface font-mono"
          />
          <NeoButton onClick={handleSearch} disabled={loading}>
            <Search size={18} className="mr-2" />
            {loading ? t('loading', lang) : t('search', lang)}
          </NeoButton>
        </div>
      </NeoCard>

      {results.length > 0 && (
        <div className="space-y-4">
          {results.map((result, index) => (
            <NeoCard key={index} title={result.title}>
              <div className="flex items-center gap-2 mb-3">
                <BookOpen size={16} />
                <span className="text-sm font-mono text-neo-muted">
                  Relevance: {(result.score * 100).toFixed(1)}%
                </span>
              </div>
              <p className="text-neo-text leading-relaxed">{result.content}</p>
            </NeoCard>
          ))}
        </div>
      )}

      {results.length === 0 && !loading && (
        <NeoCard>
          <div className="text-center py-12 text-neo-muted">
            <BookOpen size={48} className="mx-auto mb-4" />
            <p className="font-bold uppercase">Turtle Trading Wiki</p>
            <p className="text-sm mt-2">{t('searchPlaceholder', lang)}</p>
          </div>
        </NeoCard>
      )}
    </div>
  );
}
