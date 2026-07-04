# Requirements — pipeline_orchestration

## Functional requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| R1 | El usuario puede definir un fichero YAML de pipeline con una lista de steps | High |
| R2 | Cada step especifica: id, kit, servers, y opcionalmente sudo, params, needs | High |
| R3 | Steps sin `needs` se ejecutan en paralelo | High |
| R4 | Steps con `needs` esperan a que todos sus steps dependientes terminen con éxito | High |
| R5 | La salida stdout de cada step se parsea buscando líneas `KEY=VALUE`; esas variables quedan disponibles para steps posteriores | High |
| R6 | Los params de un step pueden referenciar outputs de steps anteriores con `{{ steps.<id>.<KEY> }}` | High |
| R7 | Si un step falla, los steps que dependen de él se marcan como `skipped` y no se ejecutan | High |
| R8 | `ikctl --pipeline <fichero.yaml>` ejecuta el pipeline completo | High |
| R9 | La salida muestra el progreso: qué steps corren, cuáles esperan, cuáles han terminado | Medium |
| R10 | El resumen final indica el estado de cada step: OK, FAILED, SKIPPED | Medium |

## Non-functional requirements

| ID | Requirement |
|----|-------------|
| NF1 | El DAG se resuelve en memoria antes de ejecutar ningún step — se detectan ciclos antes de empezar |
| NF2 | Un ciclo en las dependencias produce un error claro antes de ejecutar nada |
| NF3 | La interpolación `{{ steps.<id>.<KEY> }}` falla con mensaje claro si el step o la variable no existen |
| NF4 | No se añaden dependencias externas — usa solo stdlib + las ya existentes |

## Formato del fichero de pipeline

```yaml
name: install-kubernetes-cluster
steps:
  - id: packages
    kit: packages
    servers: all-nodes
    sudo: true
    params: [curl, wget, vim]

  - id: docker
    kit: docker
    servers: all-nodes
    sudo: true
    needs: [packages]

  - id: init-master
    kit: kubeadm_init
    servers: master
    sudo: true
    needs: [docker]

  - id: join-workers
    kit: join-in-kubes
    servers: workers
    sudo: true
    needs: [init-master]
    params:
      - "{{ steps.init-master.JOIN_TOKEN }}"
      - "{{ steps.init-master.JOIN_ENDPOINT }}"
```

## Formato de salida estructurada de un kit

Un kit puede escribir variables al stdout usando el formato `KEY=VALUE`:

```bash
# kubeadm_init/init.sh
echo "JOIN_TOKEN=$(kubeadm token create --print-join-command)"
echo "JOIN_ENDPOINT=$(hostname -I | awk '{print $1}'):6443"
```

Estas variables quedan disponibles en steps posteriores.

## Out of scope

- Condiciones (`when:`) para ejecutar steps condicionalmente
- Loops sobre grupos de servidores dentro del pipeline YAML
- Pipelines anidados (un pipeline que llama a otro)
- Timeout por step (usa los timeouts globales de ikctl)
