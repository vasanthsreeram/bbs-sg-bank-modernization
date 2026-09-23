       >>SOURCE FORMAT FREE
      *> ------------------------------------------------------------------
      *> Legacy BBS SG Bank daily batch. Flat files, line sequential, in the
      *> current working directory:
      *>   accounts.dat    one account per line:  IIIIIIII|BBBBBBBBBBBB
      *>                   8-digit account id, pipe, 12-digit balance in cents
      *>   operations.dat  one operation per line:  K|SSSSSSSS|TTTTTTTT|AAAAAAAAAAAA
      *>                   K = D (deposit) / W (withdraw) / T (transfer),
      *>                   SSSSSSSS source id, TTTTTTTT destination id,
      *>                   AAAAAAAAAAAA 12-digit unsigned amount in cents
      *> Prints to stdout, in this order:
      *>   PROCESSED=<8 digits>
      *>   REJECTED=<8 digits>
      *>   TOTAL_CENTS=<16 digits>
      *> accounts.dat is rewritten with the new balances (same path and layout).
      *>
      *> Deliberately inefficient on purpose -- this is the legacy behaviour
      *> the modernization effort is measured against:
      *>   * every operation re-opens and re-reads the entire master file to
      *>     validate itself, then re-opens it a second time to rewrite every
      *>     account, so m operations over n accounts cost O(m x n) I/O;
      *>   * each accepted operation copies the whole master file to a temp
      *>     file and back, instead of updating in place.
      *>
      *> Domain assumptions of the fixed-width 1980s ledger format: account
      *> ids are unique 8-digit values and balances/amounts fit 12 digits. A
      *> line that does not match the layout above cannot be parsed and so is
      *> counted as rejected rather than aborting the run.
      *> ------------------------------------------------------------------
identification division.
program-id. legacy-bank.
environment division.
input-output section.
file-control.
    select bank-file assign to "accounts.dat"
        organization is line sequential.
    select ops-file assign to "operations.dat"
        organization is line sequential.
    select temp-file assign to "accounts.tmp"
        organization is line sequential.
data division.
file section.
fd bank-file.
01 bank-row pic x(64).
fd ops-file.
01 ops-row pic x(64).
fd temp-file.
01 temp-row pic x(64).
working-storage section.
01 bank-end pic 9 value 0.
01 ops-end pic 9 value 0.
01 op-kind pic x.
01 from-id pic x(8).
01 to-id pic x(8).
01 amount-cents pic 9(12).
01 amount-text pic x(12).
01 balance-cents pic 9(12).
01 found-from pic 9.
01 found-to pic 9.
01 allowed-op pic 9.
01 processed-count pic 9(8) value 0.
01 rejected-count pic 9(8) value 0.
01 balance-total pic 9(16) value 0.
procedure division.
    open input ops-file
    perform until ops-end = 1
        read ops-file at end move 1 to ops-end
            not at end perform process-operation
        end-read
    end-perform
    close ops-file
    open input bank-file
    move 0 to bank-end balance-total
    perform until bank-end = 1
        read bank-file at end move 1 to bank-end
            not at end
                if bank-row(10:12) is numeric
                    add function numval(bank-row(10:12))
                        to balance-total
                end-if
        end-read
    end-perform
    close bank-file
    display "PROCESSED=" processed-count
    display "REJECTED=" rejected-count
    display "TOTAL_CENTS=" balance-total
    goback.
process-operation.
    move ops-row(1:1) to op-kind
    move ops-row(3:8) to from-id
    move ops-row(12:8) to to-id
    move ops-row(21:12) to amount-text
    move 0 to found-from found-to allowed-op
    if amount-text is not numeric or amount-text = all "0"
        add 1 to rejected-count
        exit paragraph
    end-if
    move function numval(amount-text) to amount-cents
    if op-kind not = "D" and op-kind not = "W" and
       op-kind not = "T"
        add 1 to rejected-count
        exit paragraph
    end-if
    if op-kind = "T" and from-id = to-id
        add 1 to rejected-count
        exit paragraph
    end-if
    *> Legacy bottleneck: reopen and scan the flat file for every operation.
    open input bank-file
    move 0 to bank-end
    perform until bank-end = 1
        read bank-file at end move 1 to bank-end
            not at end
                if bank-row(1:8) = from-id
                    move 1 to found-from
                    if op-kind = "D" or
                       function numval(bank-row(10:12)) >=
                           amount-cents
                        move 1 to allowed-op
                    end-if
                end-if
                if bank-row(1:8) = to-id
                    move 1 to found-to
                end-if
        end-read
    end-perform
    close bank-file
    if found-from = 0 or allowed-op = 0 or
       (op-kind = "T" and found-to = 0)
        add 1 to rejected-count
        exit paragraph
    end-if
    *> Legacy bottleneck: rewrite every account for every accepted operation.
    open input bank-file
    open output temp-file
    move 0 to bank-end
    perform until bank-end = 1
        read bank-file at end move 1 to bank-end
            not at end
                move bank-row to temp-row
                if bank-row(1:8) = from-id
                    move function numval(bank-row(10:12))
                        to balance-cents
                    if op-kind = "D"
                        add amount-cents to balance-cents
                    else
                        subtract amount-cents from balance-cents
                    end-if
                    move balance-cents to temp-row(10:12)
                end-if
                if op-kind = "T" and bank-row(1:8) = to-id
                    move function numval(bank-row(10:12))
                        to balance-cents
                    add amount-cents to balance-cents
                    move balance-cents to temp-row(10:12)
                end-if
                write temp-row
        end-read
    end-perform
    close bank-file temp-file
    open input temp-file
    open output bank-file
    move 0 to bank-end
    perform until bank-end = 1
        read temp-file at end move 1 to bank-end
            not at end
                move temp-row to bank-row
                write bank-row
        end-read
    end-perform
    close temp-file bank-file
    add 1 to processed-count.
