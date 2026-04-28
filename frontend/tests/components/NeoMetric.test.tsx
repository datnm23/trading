import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { NeoMetric } from '@/components/ui/NeoMetric';

describe('NeoMetric', () => {
  it('renders label and value', () => {
    render(<NeoMetric label="Test Label" value="123.45" variant="neutral" />);
    expect(screen.getByText('Test Label')).toBeInTheDocument();
    expect(screen.getByText('123.45')).toBeInTheDocument();
  });

  it('applies bullish variant class to container', () => {
    const { container } = render(<NeoMetric label="Profit" value="+5%" variant="bullish" />);
    expect(container.firstChild).toHaveClass('bullish');
  });

  it('applies bearish variant class to container', () => {
    const { container } = render(<NeoMetric label="Loss" value="-3%" variant="bearish" />);
    expect(container.firstChild).toHaveClass('bearish');
  });

  it('renders delta with bullish color', () => {
    render(<NeoMetric label="Profit" value="100" delta="+5%" variant="bullish" />);
    expect(screen.getByText('+5%')).toHaveClass('text-neo-bullish');
  });
});
