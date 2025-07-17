(define (domain credit_scoring)
  (:requirements :strips :typing)
  (:types task event gateway)

  (:predicates
    (StartEvent_1els7eb)
    (StartEvent_0o849un)
    (EndEvent_0rp5trg)
    (Task_16winvj)
    (Task_1fzfxey)
    (Task_0l942o9)
    (Task_07vbn2i)
    (Task_01ouvha)
    (Task_02m68xj)
    (Task_1r15hqs)
    (IntermediateCatchEvent_0yg7cuh)
    (IntermediateCatchEvent_0ujob24)
    (EventBasedGateway_02s95tm)
    (ExclusiveGateway_11dldcm)
    (ExclusiveGateway_0rtdod4)
    (ExclusiveGateway_125lzox)
    (EndEvent_0khk0tq)
    (done)
    (started)
  )

  (:action start_process
    :precondition (and (not (started)) (not (StartEvent_1els7eb)) (not (StartEvent_0o849un)))
    :effect (and (oneof (StartEvent_1els7eb) (StartEvent_0o849un)) (started))
  )

  (:action request_credit_score
    :precondition (and (StartEvent_1els7eb))
    :effect (and (EventBasedGateway_02s95tm) (not (StartEvent_1els7eb)))
  )

  (:action send_credit_score
    :precondition (and (Task_1fzfxey))
    :effect (and (EndEvent_0rp5trg) (not (Task_1fzfxey)))
  )

  (:action report_delay
    :precondition (and (IntermediateCatchEvent_0ujob24))
    :effect (and (and (ExclusiveGateway_11dldcm) (IntermediateCatchEvent_0yg7cuh)) (not (IntermediateCatchEvent_0ujob24)))
  )

  (:action send_credit_score_from_ExclusiveGateway_0rtdod4
    :precondition (and (Task_07vbn2i))
    :effect (and (ExclusiveGateway_125lzox) (not (Task_07vbn2i)))
  )

  (:action send_credit_score_from_Task_02m68xj
    :precondition (and (Task_02m68xj))
    :effect (and (ExclusiveGateway_125lzox) (not (Task_02m68xj)))
  )

  (:action report_delay_2
    :precondition (and (Task_01ouvha))
    :effect (and (Task_02m68xj) (not (Task_01ouvha)))
  )

  (:action compute_credit_score__level_2_
    :precondition (and (Task_02m68xj))
    :effect (and (Task_07vbn2i) (not (Task_02m68xj)))
  )

  (:action compute_credit_score__level_1_
    :precondition (and (StartEvent_0o849un))
    :effect (and (ExclusiveGateway_0rtdod4) (not (StartEvent_0o849un)))
  )

  (:action event_EventBasedGateway_02s95tm
    :precondition (and (EventBasedGateway_02s95tm))
    :effect (and (oneof (IntermediateCatchEvent_0ujob24) (and (IntermediateCatchEvent_0yg7cuh) (ExclusiveGateway_11dldcm))) (not (EventBasedGateway_02s95tm)))
  )

  (:action exclusive_ExclusiveGateway_11dldcm
    :precondition (and (ExclusiveGateway_11dldcm))
    :effect (and (Task_1fzfxey) (not (ExclusiveGateway_11dldcm)))
  )

  (:action exclusive_score_available_
    :precondition (and (ExclusiveGateway_0rtdod4))
    :effect (and (oneof (Task_01ouvha) (Task_07vbn2i)) (not (ExclusiveGateway_0rtdod4)))
  )

  (:action exclusive_ExclusiveGateway_125lzox
    :precondition (and (ExclusiveGateway_125lzox))
    :effect (and (EndEvent_0rp5trg) (not (ExclusiveGateway_125lzox)))
  )

  (:action goal_scoring_request_handled
    :precondition (and (EndEvent_0rp5trg))
    :effect (done)
  )

)