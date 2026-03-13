# Design System — Daki

> Guia de identidade visual para replicar o padrão estético da plataforma Daki em outros projetos.

---

## 1. Paleta de Cores

### Cores institucionais (Brand Guide)

| Token | Hex | Uso |
|---|---|---|
| `--daki-blue` | `#0069FF` | Cor primária — botões, links, destaques |
| `--daki-black` | `#000000` | Texto principal, headings |
| `--daki-white` | `#FFFFFF` | Fundo padrão, cards |
| `--daki-light-blue` | `#E5F0FF` | Fundos suaves, badges, selecionados |
| `--daki-dark-navy` | `#002559` | Footer, seções de contraste alto |
| `--daki-gray-3` | `#DCDCDC` | Bordas, separadores |
| `--daki-gray-2` | `#E6E6E6` | Bordas suaves |
| `--daki-gray-1` | `#F2F2F2` | Fundos de seção alternada |

### Escala de azuis

| Token | Hex | Uso |
|---|---|---|
| `--blue-50` | `#E5F0FF` | Focus ring, hover suave |
| `--blue-100` | `#D0E3FF` | Selected ring |
| `--blue-200` | `#A8CCFF` | Acentos leves |
| `--blue-500` | `#0069FF` | Cor primária |
| `--blue-600` | `#0055D4` | Hover de botão primário |
| `--blue-700` | `#0043A6` | Estados mais escuros |

### Escala de cinzas

| Token | Hex | Uso |
|---|---|---|
| `--gray-50` | `#FAFAFA` | Hover de botão secundário |
| `--gray-100` | `#F2F2F2` | Bordas de card, separadores suaves |
| `--gray-200` | `#E6E6E6` | Bordas de input |
| `--gray-300` | `#DCDCDC` | Bordas visíveis |
| `--gray-400` | `#A3A3A3` | Placeholder de input |
| `--gray-500` | `#737373` | Textos secundários, subtítulos |
| `--gray-600` | `#525252` | Textos de suporte |
| `--gray-700` | `#404040` | Labels, textos de formulário |
| `--gray-800` | `#262626` | Textos de alta ênfase |
| `--gray-900` | `#000000` | Texto máximo |

### Cor de sucesso (usada pontualmente)

| Hex | Uso |
|---|---|
| `#10B981` | Dot de etapa concluída (sidebar de progresso) |

---

## 2. Tipografia

### Famílias de fonte

| Variável | Fonte | Fallback | Uso |
|---|---|---|---|
| `--font-headline` | **Owners Narrow** | `Arial Narrow`, `Helvetica Neue Condensed`, `Impact`, sans-serif | Títulos, headings (h1, h2) |
| `--font-owners-text` | **Owners Text** | `Inter`, system-ui, sans-serif | Textos complementares da marca |
| `--font-body` | **Inter** | `-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `Roboto`, sans-serif | Corpo de texto, UI geral |
| `--font-mono` | **SF Mono** | `ui-monospace`, `SFMono-Regular`, `Menlo`, monospace | Código, valores técnicos |

### Arquivos de fonte (Owners)

```
public/fonts/OwnersNarrow-Black.ttf   → font-weight: 900
public/fonts/OwnersNarrow-Bold.ttf    → font-weight: 700
public/fonts/OwnersText-Regular.ttf   → font-weight: 400
```

### Classes de tipografia

```css
/* Títulos principais — Owners Narrow Black, UPPERCASE */
.font-headline {
  font-family: 'Owners Narrow', ...;
  font-weight: 900;
  text-transform: uppercase;
}

/* Subtítulos — Owners Narrow Bold, UPPERCASE */
.font-headline-bold {
  font-family: 'Owners Narrow', ...;
  font-weight: 700;
  text-transform: uppercase;
}

/* Textos de marca — Owners Text Regular */
.font-owners-text {
  font-family: 'Owners Text', ...;
  font-weight: 400;
}
```

### Escala de tamanhos (uso real no projeto)

| Contexto | Tamanho | Classe Tailwind |
|---|---|---|
| Hero h1 | 36px → 60px → 72px | `text-4xl sm:text-5xl md:text-6xl lg:text-7xl` |
| Seção h2 | 30px → 36px | `text-3xl md:text-4xl` |
| Subseção h3 | 24px → 30px | `text-2xl md:text-3xl` |
| Card h3 | 18px | `text-lg` |
| Corpo / parágrafo | 18px → 20px | `text-lg md:text-xl` |
| UI geral | 14px | `text-sm` |
| Label de seção | 12px | `text-xs` |
| Badge / caption | 13px | `text-[0.8125rem]` |

---

## 3. Espaçamento e Layout

### Grid e largura máxima

| Contexto | Valor |
|---|---|
| Container padrão | `max-w-6xl` (72rem) |
| Container texto | `max-w-4xl` (56rem) |
| Container estreito | `max-w-2xl` (42rem) |
| Padding horizontal | `px-4` (mobile) → `px-6` (sm+) |

### Alturas fixas

| Elemento | Altura |
|---|---|
| Header/Navbar | `3.5rem` (56px) |
| Sidebar desktop | `240px` de largura, `100vh` de altura |
| Mobile bottom nav | `4rem` (64px) |

### Padding de seção

| Contexto | Valor |
|---|---|
| Seção padrão (mobile) | `py-16 px-4` |
| Seção padrão (desktop) | `py-24 md:py-32` |
| Card padrão | `padding: 1.5rem` |
| Card métrica | `padding: 1.25rem` |

---

## 4. Bordas e Raios

| Elemento | Border Radius |
|---|---|
| Botão primário | `0.75rem` (12px) |
| Botão secundário / ghost | `0.5rem` (8px) |
| Card padrão | `0.75rem` (12px) |
| Card analytics | `1rem` (16px) |
| Modal | `1rem` (16px) |
| Input | `0.5rem` (8px) |
| Badge / pill | `9999px` (full round) |
| Feature card landing | `1rem` (16px) |
| Screenshot frame | `16px` |
| Mobile frame | `24px` |

### Bordas

- Cards: `1px solid var(--gray-100)`
- Inputs: `1px solid var(--gray-200)`
- Sidebar: `1px solid var(--gray-100)` (right)
- Header: `1px solid var(--gray-100)` (bottom)
- Mobile bottom nav: `1px solid var(--gray-100)` (top)

---

## 5. Sombras

| Contexto | Valor |
|---|---|
| Card hover | `0 4px 12px rgba(0, 0, 0, 0.05)` |
| Analytics card hover | `0 4px 12px rgba(0, 0, 0, 0.06)` |
| Botão primário hover | `0 4px 16px rgba(0, 105, 255, 0.3)` |
| Modal | via `backdrop-filter: blur(4px)` |
| Screenshot desktop | `0 20px 60px rgba(0,0,0,0.12), 0 8px 24px rgba(0,0,0,0.08)` |
| Glow azul sutil | `0 0 60px rgba(0,105,255,0.15), 0 0 120px rgba(0,105,255,0.08)` |
| Glow azul forte | `0 0 80px rgba(0,105,255,0.25), 0 0 160px rgba(0,105,255,0.12)` |
| Tooltip | `0 8px 24px rgba(0, 0, 0, 0.12)` |

---

## 6. Animações e Transições

### Durações

| Token | Valor | Uso |
|---|---|---|
| `--transition-fast` | `150ms` | Hover de botão, cor |
| `--transition-base` | `200ms` | Maioria das transições UI |
| `--transition-slow` | `300ms` | Fade in, scale in |

### Easing

| Token | Valor | Uso |
|---|---|---|
| `--ease-out` | `cubic-bezier(0.16, 1, 0.3, 1)` | Entradas, movimento natural |
| `--ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Indicador ativo da sidebar |

### Keyframes disponíveis

| Classe | Efeito |
|---|---|
| `.animate-fade-in` | Opacidade 0 → 1 |
| `.animate-fade-in-up` | Sobe 8px + aparece |
| `.animate-fade-in-scale` | Escala 0.95 → 1 + aparece |
| `.animate-slide-in-left` | Desloca -8px → 0 + aparece |
| `.stagger-children` | Anima filhos com delay de 50ms entre cada |

### Scroll Reveal (IntersectionObserver)

| Classe | Efeito | Aplica `.visible` para ativar |
|---|---|---|
| `.reveal` | `translateY(24px)` → 0, fade in | sim |
| `.reveal-left` | `translateX(-24px)` → 0 | sim |
| `.reveal-right` | `translateX(24px)` → 0 | sim |
| `.reveal-scale` | `scale(0.95)` → 1 | sim |

Transição de reveal: `0.7s cubic-bezier(0.16, 1, 0.3, 1)`

---

## 7. Componentes

### Botões

```css
/* Primário — azul sólido com shimmer no hover */
.btn-primary
  background: #0069FF
  color: white
  padding: 0.75rem 1.5rem
  border-radius: 0.75rem
  font-weight: 600
  font-size: 0.875rem
  /* hover: translateY(-1px) + box-shadow azul */
  /* active: scale(0.98) */
  /* disabled: cinza, sem interação */

/* Secundário — branco com borda */
.btn-secondary
  background: white
  color: #404040
  border: 1px solid #E6E6E6
  border-radius: 0.5rem
  font-weight: 500

/* Ghost — transparente */
.btn-ghost
  background: transparent
  color: #525252
  border-radius: 0.375rem
```

### Cards

```css
/* Base */
.card                 → border-radius: 0.75rem, border: 1px solid #F2F2F2

/* Com hover interativo */
.card-interactive     → translateY(-2px) no hover

/* Métrica (KPI) */
.card-metric          → padding: 1.25rem, valor em 1.75rem/semibold

/* Selecionável (wizard/opcoes) */
.card-selectable      → hover: border azul + glow; selected: bg azul claro

/* Analytics (sem borda, sombra sutil) */
.analytics-card-v2    → box-shadow: 0 1px 3px rgba(0,0,0,0.04)
```

### Inputs

```css
/* Input padrão */
.input-field
  padding: 0.625rem 0.875rem
  border: 1px solid #E6E6E6
  border-radius: 0.5rem
  font-size: 0.875rem
  focus: border-color #0069FF + box-shadow 3px azul claro

/* Input maior (formulários de cadastro) */
.input-daki
  padding: 0.75rem 1rem
  font-size: 0.9375rem (15px)
  mesmos estados de focus

/* Label */
.label-daki
  font-size: 0.875rem
  font-weight: 500
  color: #404040
  margin-bottom: 0.375rem
```

### Sidebar (Desktop)

```css
.sidebar-nav          → width: 240px, fixo, border-right
.sidebar-nav-item     → padding: 0.625rem 1rem, border-radius: 0.5rem
.sidebar-nav-item.active
  → background: #E5F0FF
  → color: #0055D4
  → indicador: 3px azul à esquerda (animado com ease-spring)
```

### Navegação Mobile

```css
.mobile-bottom-nav    → fixo, bottom-0, altura 4rem, border-top
.mobile-bottom-nav-item.active → color: #0069FF
/* tap: scale(0.95) */
```

### Modais

```css
.modal-backdrop       → rgba(0,0,0,0.4) + backdrop-filter: blur(4px)
.modal-content        → border-radius: 1rem, max-width: 32rem, centrado
```

### Badges / Tags

```css
.badge                → pill (border-radius: 9999px), 12px, font-weight: 500

/* Hero badge */
.hero-badge           → bg: #E5F0FF, color: #0069FF, border: #D0E3FF

/* Section label */
.section-label        → uppercase, tracking: 0.1em, 12px, azul, semibold
```

### Tabela

```css
.table-modern th      → uppercase, 12px, letter-spacing: 0.05em, gray-500
.table-modern td      → 14px, gray-700
/* hover de linha: bg gray-50 */
```

### Skeleton Loader

```css
.skeleton             → shimmer animado (gradiente 90deg, 1.5s infinite)
```

---

## 8. Padrões de Fundo

| Classe | Efeito |
|---|---|
| `.bg-hero-gradient` | Branco puro (fundo hero) |
| `.bg-mesh-gradient` | Radial azul 4% nos cantos |
| `.bg-cta-gradient` | `linear-gradient(180deg, white → #F2F2F2)` |
| `.bg-grid-pattern` | Grade 64×64px, linhas rgba(0,0,0,0.03) |
| `.bg-dot-pattern` | Pontos 32×32px, rgba(0,0,0,0.08) |
| `.glow-blue` | Glow azul suave ao redor do elemento |
| `.glow-blue-strong` | Glow azul forte |

**Alternância de seções:** branco (`#FFFFFF`) e cinza claro (`#F2F2F2`)

---

## 9. Grafismos Decorativos

Splashes orgânicos da marca, usados como elementos decorativos absolutos com `opacity` baixa (0.06–0.15). Dois conjuntos:

- `/grafismos/azul/Splash_azul_*.png` — para fundos brancos/claros
- `/grafismos/branco/Splash_branco_*.png` — para o footer navy

**Regras de uso:**
- Sempre `pointer-events: none; user-select: none; z-index: 0`
- Opacidade entre 6% e 15%
- Posicionados com `position: absolute`, geralmente fora do limite da seção (top/right negativos)

---

## 10. Estrutura de Layout

### App (dashboard/admin)

```
[Cabeçalho unificado — 56px fixo]
├── [Sidebar — 240px, fixo, abaixo do header]
└── [Main content — margin-left: 240px, padding-top: 56px]
```

### Landing page

```
[Header — 64px fixo, transparente → blur ao rolar]
[Hero — pt-28 md:pt-36]
[Seções alternadas branco / gray-1]
[Footer — navy #002559]
```

### Mobile

- Sidebar ocultada (`display: none`)
- Bottom navigation bar (4rem) substitui a sidebar
- Sub-tabs horizontais com scroll para sub-categorias
- Conteúdo com `padding-bottom: 5rem` para não ficar atrás do nav

---

## 11. CSS Variables — Referência Completa

Cole no seu `globals.css` para ter os tokens disponíveis:

```css
:root {
  /* Paleta Daki */
  --daki-blue: #0069FF;
  --daki-black: #000000;
  --daki-white: #FFFFFF;
  --daki-light-blue: #E5F0FF;
  --daki-dark-navy: #002559;
  --daki-gray-3: #DCDCDC;
  --daki-gray-2: #E6E6E6;
  --daki-gray-1: #F2F2F2;

  /* Aliases */
  --daki-blue-dark: #0055D4;
  --daki-blue-light: #E5F0FF;
  --daki-navy: #002559;
  --daki-gray: #737373;
  --daki-gray-light: #F2F2F2;
  --daki-border: #DCDCDC;

  /* Escala cinza */
  --gray-50: #FAFAFA;
  --gray-100: #F2F2F2;
  --gray-200: #E6E6E6;
  --gray-300: #DCDCDC;
  --gray-400: #A3A3A3;
  --gray-500: #737373;
  --gray-600: #525252;
  --gray-700: #404040;
  --gray-800: #262626;
  --gray-900: #000000;

  /* Escala azul */
  --blue-50: #E5F0FF;
  --blue-100: #D0E3FF;
  --blue-200: #A8CCFF;
  --blue-500: #0069FF;
  --blue-600: #0055D4;
  --blue-700: #0043A6;

  /* Transições */
  --transition-fast: 150ms;
  --transition-base: 200ms;
  --transition-slow: 300ms;
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);

  /* Fontes */
  --font-headline: 'Owners Narrow', 'Arial Narrow', 'Helvetica Neue Condensed', Impact, sans-serif;
  --font-owners-text: 'Owners Text', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-body: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'SF Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
}
```

---

## 12. Checklist ao iniciar um novo projeto

- [ ] Copiar os tokens CSS acima para `globals.css`
- [ ] Adicionar os arquivos de fonte Owners Narrow e Owners Text em `public/fonts/`
- [ ] Registrar `@font-face` para cada peso/arquivo
- [ ] Definir `body { font-family: var(--font-body); -webkit-font-smoothing: antialiased; }`
- [ ] Copiar as classes de componentes (botões, cards, inputs, badges) do `globals.css` original
- [ ] Copiar os keyframes e classes de animação
- [ ] Adicionar os grafismos em `public/grafismos/` se a seção de landing for necessária
- [ ] Usar `max-w-6xl mx-auto px-4` como container padrão
- [ ] Alternar fundos de seção entre `#FFFFFF` e `#F2F2F2`
- [ ] Footer com fundo `#002559` (navy)
