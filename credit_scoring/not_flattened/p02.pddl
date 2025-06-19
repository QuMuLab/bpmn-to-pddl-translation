(define (problem p02-bpmn-no-flatten)
        (:domain place_order_no_flatten)
        (:objects
    Task_01ouvha Task_02m68xj Task_07vbn2i Task_0l942o9 Task_16winvj Task_1fzfxey Task_1r15hqs - task
    EndEvent_0khk0tq EndEvent_0rp5trg IntermediateCatchEvent_0ujob24 IntermediateCatchEvent_0yg7cuh StartEvent_0o849un StartEvent_1els7eb - event
    EventBasedGateway_02s95tm ExclusiveGateway_0rtdod4 ExclusiveGateway_11dldcm ExclusiveGateway_125lzox - gateway
        )
        (:init (StartEvent_0o849un))
        (:goal (and (done)))
        )
    