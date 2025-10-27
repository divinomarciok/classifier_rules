# Tutorial de Backup e Restauração do Banco de Dados

Este tutorial explica como o arquivo `backup_banco.sql` foi criado e como você pode usá-lo para restaurar o banco de dados em um ambiente Docker com PostgreSQL.

---

## 1. Como o Backup foi Criado

O backup foi gerado utilizando a ferramenta padrão do PostgreSQL chamada `pg_dump`. Este utilitário se conecta ao banco de dados e exporta sua estrutura (tabelas, visões, etc.) e todos os seus dados para um único arquivo de texto no formato SQL.

O comando base utilizado foi semelhante a este:

```bash
pg_dump -U <usuario> -h <host> -p <porta> <nome_do_banco> -f backup_banco.sql
```

Este processo garante um backup completo e íntegro, que pode ser facilmente restaurado em qualquer outra instância do PostgreSQL.

---

## 2. Como Restaurar o Backup em um Contêiner Docker

Para restaurar o `backup_banco.sql` em seu contêiner PostgreSQL, siga os passos abaixo.

### Passo a Passo

**1. Identifique o nome do seu contêiner PostgreSQL:**

Primeiro, você precisa saber o nome ou o ID do seu contêiner que está rodando o PostgreSQL. Você pode listar todos os contêineres ativos com o comando:

```bash
docker ps
```

Procure na lista pelo contêiner do PostgreSQL e anote seu nome (geralmente algo como `meu-projeto-postgres-1`).

**2. Copie o arquivo de backup para dentro do contêiner:**

Use o comando `docker cp` para copiar o arquivo `backup_banco.sql` do seu computador para o sistema de arquivos do contêiner. Um bom lugar para colocá-lo temporariamente é a pasta `/tmp`.

```bash
# Substitua NOME_DO_SEU_CONTAINER pelo nome que você encontrou no passo anterior
docker cp backup/backup_banco.sql NOME_DO_SEU_CONTAINER:/tmp/backup_banco.sql
```

**3. Execute o comando de restauração (`psql`):**

Agora, use `docker exec` para rodar o comando `psql` dentro do contêiner. O `psql` irá ler o arquivo de backup e executar os comandos SQL para recriar as tabelas e inserir os dados.

**Atenção:** Este comando pode apagar e substituir dados existentes no banco de dados de destino. Execute com cuidado.

```bash
# Substitua NOME_DO_SEU_CONTAINER, <usuario> e <nome_do_banco> pelos valores corretos
docker exec -it NOME_DO_SEU_CONTAINER psql -U <usuario> -d <nome_do_banco> -f /tmp/backup_banco.sql
```

**Exemplo com os dados do projeto:**

Usando as credenciais conhecidas deste projeto (`user` e `market_v1`), o comando provavelmente será:

```bash
docker exec -it NOME_DO_SEU_CONTAINER psql -U user -d market_v1 -f /tmp/backup_banco.sql
```

Após a execução, seu banco de dados dentro do contêiner estará com os dados do backup.
