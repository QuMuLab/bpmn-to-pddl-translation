(define (problem p0-bpmn-no-flatten)
        (:domain place_order_no_flatten)
        (:objects
Task_05ftug5 Task_0e6hvnj Task_0jsoxba Task_0s79ile Task_0sl26uo Task_0vaxgaa Task_12j0pib - task
    EndEvent_1fx9yp3 StartEvent_1 test1 test2 - event
    ExclusiveGateway_0z5sib0 ExclusiveGateway_1mpgzhg ExclusiveGateway_1ouv9kf InclusiveGateway_0p2e5vq InclusiveGateway_1dgb4sg ParallelGateway_02fgrfq decrease_InclusiveGateway_0p2e5vq inclusive_counter_InclusiveGateway_0p2e5vq_0 inclusive_counter_InclusiveGateway_0p2e5vq_1 inclusive_counter_InclusiveGateway_0p2e5vq_2 increase_InclusiveGateway_0p2e5vq - gateway
        )
        (:init (inclusive_counter_InclusiveGateway_0p2e5vq_0))
        (:goal (and (done)))
        )
