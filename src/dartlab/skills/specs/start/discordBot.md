---
id: start.discordBot
title: Discord Bot — community 채널 진입점
kind: curated
scope: builtin
status: drafted
category: start
purpose: dartlab Discord bot 통합 패턴 — community 채널에서 slash command + thread 답변 + 일일 cadence 자동 발송. 외부 표면 확장.
whenToUse:
  - discord bot
  - community 채널
  - slash command discord
  - daily digest discord
inputs:
  - discord webhook / bot token
  - 사용자 message 또는 schedule
outputs:
  - thread 답변 + embed
toolRefs: []
knowledgeRefs:
  - start.dartlabSkillOs
  - start.slashCommands
sourceRefs:
  - dartlab://skills/start.discordBot
requiredEvidence:
  - skillRef
  - executionRef
runtimeCompatibility:
  server:
    status: limited
  localPython:
    status: limited
  mcp:
    status: limited
  webAi:
    status: limited
  pyodide:
    status: limited
linkedSkills:
  - start.dartlabSkillOs
  - start.slashCommands
---

## 통합 패턴

### 1. slash command (이미 start.slashCommands)

Discord 측 slash command 등록 → dartlab API 호출.

### 2. mention 답변

```python
@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message):
        result = dartlab.ask(message.content)
        await message.channel.send(result.text, embeds=result.embeds)
```

### 3. 일일 cadence (cron)

```python
@tasks.loop(hours=24)
async def daily_morning_note():
    result = dartlab.ask("오늘 아침 브리핑")
    await channel.send(embed=embed_from_result(result))
```

## 강행 룰

1. bot token secret store (env var, 코드 hardcode 금지).
2. 사용자 input → untrusted wrap (community 채널 = 외부 본문).
3. evidence GATE 통과 후 답변 (citation format inline).
4. rate limit 강행 (per-user / per-channel).

## 안티패턴

- bot token 로그 출력.
- 사용자 input 직접 eval / exec.
- evidence GATE 우회 답변.

## 기본 검증

- token secret store 확인.
- rate limit metric.
- evidence GATE 통과 비율.
