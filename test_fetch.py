import sys
sys.path.insert(0, '.')
from fetchers.pubmed import PubMedFetcher

f = PubMedFetcher(source_name='PubMed', max_results=20)
papers = f.fetch(['wheat rust', 'wheat resistance', 'Puccinia'], 7)
for p in papers:
    print(p.title[:80])
print('共', len(papers), '篇')