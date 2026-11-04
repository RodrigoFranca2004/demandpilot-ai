import { useEffect, useRef, useState, type FormEvent } from 'react'
import ReactMarkdown from 'react-markdown'

import { askAdvisor } from '../api/advisor'
import './AdvisorChat.css'

interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
}

interface AdvisorChatProps {
  restaurantId: number
}

const EXAMPLE_QUESTIONS = [
  'Quais ingredientes apresentam risco de falta hoje?',
  'Qual modelo foi selecionado para prever a demanda do Classic Burger?',
  'Quais produtos apresentam maior demanda prevista?',
]

export function AdvisorChat({ restaurantId }: AdvisorChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const nextMessageId = useRef(1)
  const pendingRequest = useRef<AbortController | null>(null)
  const messagesContainer = useRef<HTMLDivElement | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  useEffect(() => {
    return () => {
      pendingRequest.current?.abort()
    }
  }, [])

  useEffect(() => {
    if (messages.length === 0) {
      return
    }

    const container = messagesContainer.current

    if (container) {
      container.scrollTop = container.scrollHeight
    }
  }, [messages, sending])

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault()

    const question = draft.trim()

    if (
      !question ||
      question.length > 1000 ||
      pendingRequest.current
    ) {
      return
    }

    const controller = new AbortController()
    pendingRequest.current = controller

    const userMessage: ChatMessage = {
      id: nextMessageId.current++,
      role: 'user',
      content: question,
    }

    setMessages((current) => [...current, userMessage])
    setDraft('')
    setError(null)
    setSending(true)

    try {
      const answer = await askAdvisor(
        restaurantId,
        question,
        controller.signal,
      )

      if (controller.signal.aborted) {
        return
      }

      const assistantMessage: ChatMessage = {
        id: nextMessageId.current++,
        role: 'assistant',
        content: answer,
      }

      setMessages((current) => [
        ...current,
        assistantMessage,
      ])
    } catch (caughtError) {
      if (!controller.signal.aborted) {
        setError(
          caughtError instanceof Error
            ? caughtError.message
            : 'Ocorreu um erro ao consultar o assistente.',
        )
      }
    } finally {
      if (pendingRequest.current === controller) {
        pendingRequest.current = null

        if (!controller.signal.aborted) {
          setSending(false)
        }
      }
    }
  }

  function selectQuestion(question: string): void {
    setDraft(question)
    textareaRef.current?.focus()
  }

  return (
    <section
      className="advisor-section"
      aria-labelledby="advisor-title"
    >
      <div className="section-heading">
        <div>
          <div className="eyebrow">GENERATIVE AI</div>
          <h2 id="advisor-title">Assistente de IA</h2>
        </div>

        <span className="section-note">
          Gemini + Tool Calling
        </span>
      </div>

      <div className="advisor-workspace">
        <div className="advisor-header">
          <div className="advisor-avatar" aria-hidden="true">
            AI
          </div>

          <div className="advisor-heading">
            <h3>DemandPilot Advisor</h3>
            <p>
              Consulte previsões de demanda e riscos de estoque.
            </p>
          </div>
        </div>

        <div className="advisor-conversation">
          {messages.length === 0 ? (
            <div className="advisor-welcome">
              <div className="advisor-welcome-icon" aria-hidden="true">
                ✨
              </div>

              <h3>Como posso ajudar?</h3>

              <p>
                Pergunte sobre a demanda prevista, os ingredientes
                necessários ou possíveis faltas de estoque.
              </p>
            </div>
          ) : (
            <div
              className="advisor-messages"
              ref={messagesContainer}
              aria-label="Mensagens do assistente"
              aria-live="polite"
            >
              {messages.map((message) => (
                <div
                  className={`advisor-message advisor-message--${message.role}`}
                  key={message.id}
                >
                  <div className="advisor-message-label">
                    {message.role === 'user'
                      ? 'Você'
                      : 'DemandPilot AI'}
                  </div>

                  <div className="advisor-message-content">
                    {message.role === 'assistant' ? (
                      <ReactMarkdown>
                        {message.content}
                      </ReactMarkdown>
                    ) : (
                      <p>{message.content}</p>
                    )}
                  </div>
                </div>
              ))}

              {sending && (
                <div
                  className="advisor-typing"
                  role="status"
                >
                  <span
                    className="advisor-loading-dot"
                    aria-hidden="true"
                  />
                  Consultando dados e gerando resposta...
                </div>
              )}
            </div>
          )}
        </div>

        <div className="advisor-suggestions">
          <span>Sugestões de perguntas</span>

          <div className="advisor-suggestion-list">
            {EXAMPLE_QUESTIONS.map((question) => (
              <button
                className="advisor-suggestion"
                key={question}
                type="button"
                disabled={sending}
                onClick={() => selectQuestion(question)}
              >
                {question}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <p className="advisor-error" role="alert">
            {error}
          </p>
        )}

        <form
          className="advisor-composer"
          onSubmit={(event) => {
            void handleSubmit(event)
          }}
        >
          <label
            className="advisor-composer-label"
            htmlFor="advisor-question"
          >
            Sua pergunta
          </label>

          <textarea
            id="advisor-question"
            ref={textareaRef}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (
                event.key === 'Enter' &&
                !event.shiftKey &&
                !event.nativeEvent.isComposing
              ) {
                event.preventDefault()
                event.currentTarget.form?.requestSubmit()
              }
            }}
            placeholder="Ex.: Quais ingredientes preciso comprar amanhã?"
            rows={3}
            maxLength={1000}
            disabled={sending}
            required
          />

          <div className="advisor-composer-footer">
            <div className="advisor-composer-hints">
              <span>
                Enter para enviar · Shift+Enter para nova linha
              </span>
              <span>{draft.length}/1000 caracteres</span>
            </div>

            <button
              className="advisor-send-button"
              type="submit"
              disabled={!draft.trim() || sending}
            >
              {sending ? 'Consultando...' : 'Enviar pergunta'}
            </button>
          </div>
        </form>

        <p className="advisor-disclaimer">
          Cada pergunta é processada independentemente. As mensagens
          anteriores aparecem apenas nesta tela e não são enviadas
          como contexto ao Gemini. As recomendações são estimativas
          baseadas nos dados disponíveis.
        </p>
      </div>
    </section>
  )
}