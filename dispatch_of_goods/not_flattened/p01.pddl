(define (problem p01-bpmn-no-flatten)
        (:domain place_order_no_flatten)
        (:objects
    Task_05ftug5 Task_0e6hvnj Task_0jsoxba Task_0s79ile Task_0sl26uo Task_0vaxgaa Task_12j0pib branch_started_InclusiveGateway_0p2e5vq_Task_0jsoxba branch_started_InclusiveGateway_0p2e5vq_Task_12j0pib - task
    EndEvent_1fx9yp3 StartEvent_1 - event
    ExclusiveGateway_0z5sib0 ExclusiveGateway_1mpgzhg ExclusiveGateway_1ouv9kf InclusiveGateway_0p2e5vq InclusiveGateway_1dgb4sg ParallelGateway_02fgrfq at_least_one_branch_InclusiveGateway_0p2e5vq branch_started_InclusiveGateway_0p2e5vq_Task_0jsoxba branch_started_InclusiveGateway_0p2e5vq_Task_12j0pib - gateway
        )
        (:init (StartEvent_1))
        (:goal (and (done)))
        )
    