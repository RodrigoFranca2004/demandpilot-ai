export async function askAdvisor(
  restaurantId: number,
  question: string,
  signal: AbortSignal,
): Promise<string> {
  let response: Response

  try {
    response = await fetch(
      `/api/restaurants/${restaurantId}/advisor/chat`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: question }),
        signal,
      },
    )
  } catch (error) {
    if (signal.aborted) {
      throw error
    }

    throw new Error(
      'Não foi possível conectar ao servidor. Verifique se a API está disponível.',
      {cause: error},
    )
  }

  if (!response.ok) {
    const errorMessages: Record<number, string> = {
      404: 'Restaurante não encontrado.',
      422: 'Não foi possível processar a pergunta. Verifique os dados disponíveis.',
      429: 'O limite de requisições do assistente foi atingido. Tente novamente mais tarde.',
      502: 'O Gemini não conseguiu gerar uma resposta válida.',
      503: 'O serviço de IA está indisponível. Verifique a configuração da API.',
      504: 'O assistente demorou para responder. Tente novamente.',
    }

    throw new Error(
      errorMessages[response.status] ??
        `Não foi possível obter uma resposta (HTTP ${response.status}).`,
    )
  }

  let data: unknown

  try {
    data = await response.json()
  } catch {
    throw new Error('O servidor retornou uma resposta inválida.')
  }

  if (
    typeof data !== 'object' ||
    data === null ||
    !('answer' in data) ||
    typeof data.answer !== 'string' ||
    !data.answer.trim()
  ) {
    throw new Error('O assistente retornou uma resposta inesperada.')
  }

  return data.answer.trim()
}
