# lucasjesus-posts

O Instagram **@lucasjesus.oficial** no piloto automático: um post por dia, às 18h, no feed e no story, criado por um squad de agentes e publicado pela API oficial da Meta. Sem aprovação.

## Como funciona

| Quem | Quando | O quê |
|---|---|---|
| **Radar de IA** (GitHub) | todo dia, 05:50 | lê os feeds oficiais (OpenAI, Google, DeepMind, Hugging Face, Microsoft, NVIDIA) e a imprensa de tecnologia e grava `radar/AAAA-MM-DD.json` |
| **Squad** (rotina diária do Claude) | todo dia, ~14h | estrategista, pesquisador, copywriter, diretor de arte e revisor criam o post do dia e salvam em `posts/AAAA-MM-DD/` |
| **Gerar imagem (GPT)** (GitHub) | quando o squad pede | gera ingredientes de imagem com a API oficial da OpenAI (sem texto) |
| **Publicar no Instagram** (GitHub) | a cada 5 min | publica no horário exato: post único, carrossel ou Reels, mais o story |
| **Métricas** (GitHub) | segundas, 07:20 | lê alcance, salvamentos e compartilhamentos para o Analista ajustar a estratégia |

Regras do squad em `agentes/` (comece por `squad.md`). Sistema visual em `agentes/marca.md` e `kit/render.py`.

### Por que não tem cara de IA

A arte é montada em código (tipografia, grid e paleta próprios), com as **suas fotos reais**. O GPT só gera ingredientes (objeto, cenário), que recebem tratamento de revista (duotone e grão). O texto passa por um revisor que barra os vícios de escrita de IA.

## O que você faz

- **Fotos:** suba em `fotos/novas/` (Add file > Upload files). O squad cataloga sozinho.
- **Ideias:** escreva em `pautas/ideias.md`. Têm prioridade sobre o calendário.
- **Cancelar um post:** em `posts/AAAA-MM-DD/post.json`, troque `"status": "agendado"` por `"cancelado"`.
- **Mudar o calendário ou o tom:** edite `agentes/calendario.md` e `agentes/voz.md`.

## Estrutura de um post

```
posts/2026-10-20/
  arte.json    textos e modelos (o render lê isto)
  01.jpg …     artes do feed, 1080x1350 (2 ou mais = carrossel)
  story.jpg    1080x1920
  post.json    {"publicar_em": "2026-10-20T18:00:00-03:00", "legenda": "...", "story": true, "status": "agendado"}
```

## Configuração (uma vez)

O Instagram precisa ser **profissional** (Criador de conteúdo serve).

### 1. Token da Meta (login com Instagram)

1. Em **developers.facebook.com**, abra o seu app (pode ser o mesmo "Publicador Conexão") > **Instagram** > **Configuração da API com login do Instagram**.
2. Em "Gerar tokens de acesso", clique em **Adicionar conta** e entre com o **@lucasjesus.oficial**.
3. Clique em **Gerar token** ao lado da conta e copie (começa com `IG`).
   Permissões usadas: `instagram_business_basic`, `instagram_business_content_publish`, `instagram_business_manage_insights`.

### 2. Segredos do GitHub

Neste repositório: **Settings > Secrets and variables > Actions > New repository secret**:

| Nome | Valor |
|---|---|
| `META_TOKEN` | o token do passo 1 |
| `OPENAI_API_KEY` | sua chave da API da OpenAI (platform.openai.com > API keys) |
| `GH_PAT` | token do GitHub com permissão de **Secrets: read and write** neste repositório (github.com/settings/personal-access-tokens). Serve para o token da Meta se renovar sozinho a cada semana. |

`IG_USER_ID` não é necessário com o token de login com Instagram.

### 3. Testar

**Actions > Publicar no Instagram > Run workflow**, marque "Só testar a conexão". O log deve mostrar `Conectado: @lucasjesus.oficial`.

Depois rode **Actions > Radar de IA > Run workflow** para gerar o primeiro radar.
